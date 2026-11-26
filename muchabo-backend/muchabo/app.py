"""HTTP boundary and application-owned resources for the shared runtime."""

import asyncio
import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID, uuid4

from ag_ui.core import RunAgentInput
from fastapi import FastAPI
from httpx import AsyncClient
from openai import AsyncOpenAI
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import Message

from . import telemetry
from .agent import CallerContext, reply
from .bot_spec import BODY_LIMIT, PublicError, fetch_bot, identifier_adapter
from .settings import load_settings


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None]:
    """Validate settings and retain clients/tracing until active responses drain."""
    settings = load_settings()
    application.title = settings.app_name
    langfuse, provider, instrumentation = telemetry.initialize(settings)
    application.state.settings = settings
    application.state.instrumentation = instrumentation
    application.state.provider = provider
    application.state.langfuse = langfuse
    application.state.active_streams = 0
    application.state.streams_drained = asyncio.Event()
    application.state.streams_drained.set()
    try:
        async with (
            AsyncClient(base_url=settings.admin_base_url.get_secret_value(), timeout=5, follow_redirects=False, trust_env=False) as admin,
            AsyncOpenAI(
                base_url=settings.litellm_base_url.get_secret_value(),
                api_key=settings.litellm_api_key.get_secret_value(),
                max_retries=0,
                timeout=20,
            ) as gateway,
        ):
            application.state.admin = admin
            application.state.gateway = gateway
            try:
                yield
            finally:
                await application.state.streams_drained.wait()
    finally:
        await telemetry.shutdown(langfuse, provider)


app = FastAPI(title="muchabo backend", lifespan=lifespan)


@app.get("/api/healthz")
async def healthz() -> dict[str, str]:
    """Report liveness without accessing configuration or models."""
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, str]:
    """Return the existing operational greeting."""
    return {"message": "muchabo backend is running"}


def accepts_sse(value: str) -> bool:
    """Honor explicit media-range quality values when negotiating SSE."""
    qualities: dict[str, float] = {}
    for item in value.split(","):
        media, *parameters = item.strip().lower().split(";")
        quality = 1.0
        for parameter in parameters:
            if parameter.strip().startswith("q="):
                try:
                    quality = float(parameter.strip()[2:])
                except ValueError:
                    quality = 0
        qualities[media] = quality if 0 <= quality <= 1 else 0
    return qualities.get("text/event-stream", qualities.get("text/*", qualities.get("*/*", 0))) > 0


def validate_input(data: object) -> RunAgentInput:
    """Enforce the strict single-text-message scope before native protocol parsing."""
    required = {"threadId", "runId", "messages", "state", "tools", "context"}
    if not isinstance(data, dict) or not required <= set(data) or set(data) - required - {"forwardedProps"}:
        raise ValueError("Invalid request")
    for key in ("threadId", "runId"):
        if not isinstance(data[key], str):
            raise ValueError("Invalid correlation identifier")
        UUID(data[key])
    if (
        type(data["state"]) is not dict
        or data["state"]
        or type(data.get("forwardedProps", {})) is not dict
        or data.get("forwardedProps", {})
    ):
        raise ValueError("Unsupported state")
    if data["tools"] != [] or data["context"] != []:
        raise ValueError("Unsupported tools or context")
    messages = data["messages"]
    if not isinstance(messages, list) or len(messages) != 1:
        raise ValueError("Exactly one user message is required")
    message = messages[0]
    if not isinstance(message, dict) or set(message) != {"id", "role", "content"} or message["role"] != "user":
        raise ValueError("Invalid user message")
    if not isinstance(message["id"], str):
        raise ValueError("Invalid message identifier")
    UUID(message["id"])
    if not isinstance(message["content"], str) or not message["content"].strip() or len(message["content"]) > 16000:
        raise ValueError("Invalid message content")
    return RunAgentInput.model_validate(data)


@app.post("/api/bots/{bot_id}/run")
async def run_bot(bot_id: str, request: Request) -> Response:
    """Validate transport/input/access, fetch a current spec and deliver one native run."""
    request_id = str(uuid4())
    attributes = {"request_id": request_id}

    def reject(status: int, code: telemetry.DiagnosticCode, message: str) -> JSONResponse:
        telemetry.diagnostic(code, attributes)
        return JSONResponse(
            {"code": code, "message": message, "request_id": request_id}, status_code=status, headers={"X-Request-ID": request_id}
        )

    if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
        return reject(415, "UNSUPPORTED_MEDIA_TYPE", "Send the request as application/json.")
    if not accepts_sse(request.headers.get("accept", "")):
        return reject(406, "UNSUPPORTED_RESPONSE_TYPE", "Accept text/event-stream responses.")
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > BODY_LIMIT:
            return reject(413, "REQUEST_TOO_LARGE", "The request is too large.")
        body.extend(chunk)
    try:
        identifier_adapter.validate_python(bot_id)
        native_input = validate_input(json.loads(body))
    except ValueError, ValidationError, UnicodeDecodeError, RecursionError:
        return reject(422, "INVALID_REQUEST", "Send one non-empty user text message with valid UUID identifiers.")
    attributes.update({"bot_id": bot_id, "conversation_id": native_input.thread_id, "session_id": native_input.thread_id})
    try:
        spec = await fetch_bot(
            request.app.state.admin, bot_id, request.app.state.settings.admin_access_token.get_secret_value(), request_id
        )
    except PublicError as error:
        return reject(error.status, error.code, error.message)
    attributes.update({"bot_version": spec.version, "model_alias": spec.agent.model or ""})
    if spec.access_policy != "anonymous":
        return reject(403, "ACCESS_DENIED", "This bot is not available for anonymous access.")

    async def receive() -> Message:
        return {"type": "http.request", "body": bytes(body), "more_body": False}

    # Replay the already bounded/validated body through the native adapter's public request API.
    native_request = Request(request.scope, receive=receive)
    context = CallerContext(request_id=request_id, conversation_id=native_input.thread_id, session_id=native_input.thread_id)
    return await reply(native_request, spec, context)
