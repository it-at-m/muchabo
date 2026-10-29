"""Request-local native execution, anonymous dependencies and terminal sanitization."""

from collections.abc import AsyncGenerator
from contextlib import aclosing
from dataclasses import dataclass
from time import monotonic
from typing import Literal, cast
from uuid import uuid4

from ag_ui.core import BaseEvent, EventType, RunErrorEvent
from langfuse import propagate_attributes
from opentelemetry.trace import StatusCode
from pydantic_ai import Agent, RunCancelled, RunTimedOut
from pydantic_ai.capabilities import Instrumentation
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.litellm import LiteLLMProvider
from pydantic_ai.ui.ag_ui import AGUIAdapter
from starlette.requests import Request
from starlette.responses import StreamingResponse

from . import telemetry
from .bot_spec import BotSpec

RUN_TIMEOUT = 30


@dataclass(frozen=True, kw_only=True)
class CallerContext:
    """Server-set public identity; caller correlation inputs confer no permissions."""

    request_id: str
    conversation_id: str
    session_id: str
    access_policy: Literal["anonymous"] = "anonymous"
    user_id: None = None
    tenant: Literal["public"] = "public"
    roles: tuple[()] = ()


def failure(code: Literal["RUN_FAILED", "RUN_TIMEOUT"]) -> RunErrorEvent:
    """Create a fresh protocol error with fixed public text and no native payload."""
    return RunErrorEvent(
        code=code,
        message={
            "RUN_FAILED": "The agent could not complete your request. Please try again.",
            "RUN_TIMEOUT": "The agent took too long to respond. Please try again.",
        }[code],
    )


async def reply(request: Request, spec: BotSpec, context: CallerContext) -> StreamingResponse:
    """Prepare native AG-UI encoding while execution resources live inside body consumption."""
    state = request.app.state
    model_alias = cast(str, spec.agent.model)
    model = OpenAIChatModel(model_alias, provider=LiteLLMProvider(openai_client=state.gateway))
    agent: Agent[CallerContext, str] = Agent.from_spec(
        spec.agent,
        model=model,
        name=spec.bot_id,
        deps_type=CallerContext,
        retries=0,
        model_settings={"request_timeout": 25},
        capabilities=[Instrumentation(settings=state.instrumentation)],
    )
    adapter = await AGUIAdapter[CallerContext, str].from_request(request, agent=agent)
    attributes = {
        "bot_id": spec.bot_id,
        "bot_version": spec.version,
        "model_alias": model_alias,
        "request_id": context.request_id,
        "conversation_id": context.conversation_id,
        "session_id": context.session_id,
    }

    async def on_cancel(cancelled: RunCancelled) -> AsyncGenerator[BaseEvent]:
        if isinstance(cancelled, RunTimedOut):
            yield failure("RUN_TIMEOUT")

    async def consume() -> AsyncGenerator[BaseEvent]:
        started = monotonic()
        terminal = False
        outcome: telemetry.DiagnosticCode = "RUN_CANCELLED"
        tracer = state.provider.get_tracer("muchabo.runtime")
        try:
            with (
                propagate_attributes(session_id=context.session_id, version=spec.version, metadata=attributes, as_baggage=False),
                tracer.start_as_current_span(
                    "agent_request", attributes=attributes, record_exception=False, set_status_on_exception=False
                ) as span,
            ):
                try:
                    async with agent:
                        stream = cast(
                            AsyncGenerator[BaseEvent],
                            adapter.run_stream(
                                deps=context,
                                metadata=attributes,
                                run_id=str(uuid4()),
                                conversation_id=context.conversation_id,
                                timeout=RUN_TIMEOUT,
                                infer_name=False,
                                on_cancel=on_cancel,
                            ),
                        )
                        async with aclosing(stream):
                            async for event in stream:
                                if terminal:
                                    continue
                                if event.type == EventType.RUN_ERROR:
                                    code = (
                                        "RUN_TIMEOUT" if isinstance(event, RunErrorEvent) and event.code == "RUN_TIMEOUT" else "RUN_FAILED"
                                    )
                                    outcome = code
                                    terminal = True
                                    span.set_status(StatusCode.ERROR)
                                    yield failure(code)
                                else:
                                    if event.type == EventType.RUN_FINISHED:
                                        terminal = True
                                        outcome = "RUN_FINISHED"
                                    yield event
                except Exception:
                    span.set_status(StatusCode.ERROR)
                    if not terminal:
                        outcome = "RUN_FAILED"
                        terminal = True
                        yield failure("RUN_FAILED")
                finally:
                    span.set_attribute("event_code", outcome)
                    span.set_attribute("duration_ms", (monotonic() - started) * 1000)
        finally:
            telemetry.diagnostic(outcome, attributes, (monotonic() - started) * 1000)
            state.active_streams -= 1
            if state.active_streams == 0:
                state.streams_drained.set()

    response = adapter.streaming_response(consume())
    response.headers["X-Request-ID"] = context.request_id
    response.headers["Cache-Control"] = "no-store"
    state.active_streams += 1
    state.streams_drained.clear()
    return response
