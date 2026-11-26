"""HTTP/AG-UI contract, bounded failures and isolated native execution checks."""

import asyncio
import copy
import json
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
from ag_ui.core import Event, EventType
from pydantic import TypeAdapter
from pydantic_ai import RunContext
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.function import AgentInfo, FunctionModel
from starlette.types import Message


def events(response: httpx.Response) -> list[Any]:
    """Parse every SSE data event through the native protocol union."""
    assert response.status_code == 200, response.text
    return [TypeAdapter(Event).validate_json(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]


async def test_controlled_reply(client: httpx.AsyncClient, payload: dict[str, Any]) -> None:
    response = await client.post("/api/bots/demo/run", json=payload, headers={"Accept": "text/event-stream"})
    parsed = events(response)
    assert "".join(event.delta for event in parsed if event.type == EventType.TEXT_MESSAGE_CONTENT) == "Hello."
    assert sum(event.type == EventType.RUN_FINISHED for event in parsed) == 1
    assert not any(event.type == EventType.RUN_ERROR for event in parsed)
    assert parsed[0].thread_id == payload["threadId"]
    UUID(response.headers["X-Request-ID"])
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("threadId", "not-a-uuid"),
        ("runId", 1),
        ("messages", []),
        ("messages", [{}, {}]),
        ("state", []),
        ("state", {"secret": "private"}),
        ("tools", None),
        ("tools", [{}]),
        ("context", [{}]),
        ("forwardedProps", None),
        ("forwardedProps", {"roles": ["employee"]}),
        ("roles", ["employee"]),
        ("protocolVersion", "1.0"),
    ],
)
async def test_invalid_top_level(client: httpx.AsyncClient, payload: dict[str, Any], field: str, value: object) -> None:
    from muchabo.app import app

    payload[field] = value
    response = await client.post("/api/bots/demo/run", json=payload, headers={"Accept": "text/event-stream"})
    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_REQUEST"
    assert not app.state.admin_requests
    assert app.state.controlled_model.last_model_request_parameters is None
    assert "private" not in response.text


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("content", ""),
        ("content", " \n"),
        ("content", "a" * 16001),
        ("content", None),
        ("content", [{"type": "text", "text": "hi"}]),
        ("id", "bad"),
        ("id", 1),
        ("role", "assistant"),
        ("role", "system"),
        ("role", "tool"),
        ("name", "private"),
        ("metadata", {"secret": "private"}),
    ],
)
async def test_invalid_message(client: httpx.AsyncClient, payload: dict[str, Any], field: str, value: object) -> None:
    from muchabo.app import app

    payload["messages"][0][field] = value
    response = await client.post("/api/bots/demo/run", json=payload, headers={"Accept": "text/event-stream"})
    assert response.status_code == 422
    assert not app.state.admin_requests
    assert app.state.controlled_model.last_model_request_parameters is None


@pytest.mark.parametrize(
    ("body", "headers", "status"),
    [
        (b"{", {"Content-Type": "application/json", "Accept": "text/event-stream"}, 422),
        (b"[" * 2000 + b"0" + b"]" * 2000, {"Content-Type": "application/json", "Accept": "text/event-stream"}, 422),
        (b"{}", {"Content-Type": "text/plain", "Accept": "text/event-stream"}, 415),
        (b"{}", {"Content-Type": "application/json", "Accept": "application/json"}, 406),
        (b"{}", {"Content-Type": "application/json", "Accept": "text/event-stream;q=0"}, 406),
        (b" " * 65537, {"Content-Type": "application/json", "Accept": "text/event-stream"}, 413),
    ],
)
async def test_transport_rejections(client: httpx.AsyncClient, body: bytes, headers: dict[str, str], status: int) -> None:
    from muchabo.app import app

    response = await client.post("/api/bots/demo/run", content=body, headers=headers)
    assert response.status_code == status
    assert not app.state.admin_requests
    assert app.state.controlled_model.last_model_request_parameters is None
    assert response.json()["request_id"] == response.headers["x-request-id"]


async def test_authenticated_bot_denied(client: httpx.AsyncClient, bot: dict[str, Any], payload: dict[str, Any]) -> None:
    from muchabo.app import app

    bot["access_policy"] = "authenticated"
    response = await client.post(
        "/api/bots/demo/run",
        json=payload,
        headers={
            "Accept": "text/event-stream",
            "Authorization": "Bearer caller",
            "X-Roles": "employee",
            "X-User-ID": "private",
        },
    )
    assert response.status_code == 403
    assert response.json()["code"] == "ACCESS_DENIED"
    assert app.state.controlled_model.last_model_request_parameters is None


async def test_execution_failure_is_sanitized(
    client: httpx.AsyncClient,
    payload: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from muchabo import agent

    async def failing(messages: list[ModelMessage], info: AgentInfo) -> AsyncGenerator[str]:
        raise RuntimeError("distinct-private-exception-secret")
        yield "unreachable"

    monkeypatch.setattr(agent, "OpenAIChatModel", lambda *args, **kwargs: FunctionModel(stream_function=failing))
    response = await client.post("/api/bots/demo/run", json=payload, headers={"Accept": "text/event-stream"})
    parsed = events(response)
    errors = [event for event in parsed if event.type == EventType.RUN_ERROR]
    assert len(errors) == 1
    assert errors[0].code == "RUN_FAILED"
    assert errors[0].message == "The agent could not complete your request. Please try again."
    assert not any(event.type == EventType.RUN_FINISHED for event in parsed)
    assert "distinct-private" not in response.text


async def test_timeout_has_no_success(
    client: httpx.AsyncClient,
    payload: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from muchabo import agent

    cleaned = asyncio.Event()

    async def delayed(messages: list[ModelMessage], info: AgentInfo) -> AsyncGenerator[str]:
        try:
            await asyncio.sleep(31)
            yield "too late"
        finally:
            cleaned.set()

    monkeypatch.setattr(agent, "OpenAIChatModel", lambda *args, **kwargs: FunctionModel(stream_function=delayed))
    monkeypatch.setattr(agent, "RUN_TIMEOUT", 0.05)
    parsed = events(await client.post("/api/bots/demo/run", json=payload, headers={"Accept": "text/event-stream"}))
    assert [event.code for event in parsed if event.type == EventType.RUN_ERROR] == ["RUN_TIMEOUT"]
    assert not any(event.type == EventType.RUN_FINISHED for event in parsed)
    assert cleaned.is_set()


@pytest.mark.parametrize(("status", "expected"), [(404, 404), (401, 503), (503, 503), (200, 502)])
async def test_configuration_errors_before_streaming(
    client: httpx.AsyncClient,
    payload: dict[str, Any],
    status: int,
    expected: int,
) -> None:
    from muchabo.app import app

    async with httpx.AsyncClient(
        base_url="http://localhost",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(status, text="producer-private-secret"),
        ),
    ) as admin:
        app.state.admin = admin
        response = await client.post("/api/bots/demo/run", json=payload, headers={"Accept": "text/event-stream"})
    assert response.status_code == expected
    assert "producer-private" not in response.text
    assert app.state.active_streams == 0
    assert app.state.controlled_model.last_model_request_parameters is None


async def test_ten_successes_and_ten_isolated_concurrent_runs(
    client: httpx.AsyncClient,
    payload: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from muchabo import agent
    from muchabo.app import app

    contexts: list[agent.CallerContext] = []

    @dataclass
    class CaptureContext(AbstractCapability[agent.CallerContext]):
        async def before_run(self, ctx: RunContext[agent.CallerContext]) -> None:
            contexts.append(ctx.deps)

    original = agent.Agent.from_spec

    def capture_spec(*args: Any, **kwargs: Any) -> Any:
        kwargs["capabilities"] = [*kwargs["capabilities"], CaptureContext()]
        return original(*args, **kwargs)

    monkeypatch.setattr(agent.Agent, "from_spec", capture_spec)

    async def echo(messages: list[ModelMessage], info: AgentInfo) -> AsyncGenerator[str]:
        assert not info.function_tools and not info.output_tools
        assert info.model_settings and info.model_settings["request_timeout"] == 25
        prompts = [part.content for message in messages for part in message.parts if part.part_kind == "user-prompt"]
        assert len(prompts) == 1
        await asyncio.sleep(0.01)
        yield str(prompts[0])

    monkeypatch.setattr(agent, "OpenAIChatModel", lambda *args, **kwargs: FunctionModel(stream_function=echo))

    async def interaction(index: int) -> None:
        request = copy.deepcopy(payload)
        request["threadId"], request["runId"] = str(uuid4()), str(uuid4())
        request["messages"][0]["id"] = str(uuid4())
        request["messages"][0]["content"] = f"isolated-message-{index}"
        response = await client.post(
            "/api/bots/demo/run",
            json=request,
            headers={
                "Accept": "text/event-stream",
                "X-User-ID": "employee",
                "X-Roles": "admin",
                "X-Tenant": "internal",
            },
        )
        parsed = events(response)
        assert "".join(event.delta for event in parsed if event.type == EventType.TEXT_MESSAGE_CONTENT) == f"isolated-message-{index}"
        assert sum(event.type == EventType.RUN_FINISHED for event in parsed) == 1
        assert not any(event.type == EventType.RUN_ERROR for event in parsed)

    for index in range(10):
        await interaction(index)
    await asyncio.gather(*(interaction(index) for index in range(10, 20)))
    assert len(contexts) == 20
    assert len({context.request_id for context in contexts}) == 20
    assert len({context.conversation_id for context in contexts}) == 20
    for context in contexts:
        assert context.session_id == context.conversation_id
        assert context.roles == () and context.user_id is None
        assert context.tenant == "public" and context.access_policy == "anonymous"
    assert app.state.active_streams == 0
    assert app.state.streams_drained.is_set()


async def test_inflight_version_retained_on_configuration_refresh(
    client: httpx.AsyncClient,
    payload: dict[str, Any],
    bot: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    collector: Any,
) -> None:
    from muchabo import agent
    from muchabo.app import app

    first_running = asyncio.Event()
    release_first = asyncio.Event()
    bot["agent"]["instructions"] = "instructions-v1"

    async def configured(messages: list[ModelMessage], info: AgentInfo) -> AsyncGenerator[str]:
        if info.instructions == "instructions-v1":
            first_running.set()
            await release_first.wait()
        yield info.instructions or ""

    monkeypatch.setattr(agent, "OpenAIChatModel", lambda *args, **kwargs: FunctionModel(stream_function=configured))
    first = asyncio.create_task(client.post("/api/bots/demo/run", json=payload, headers={"Accept": "text/event-stream"}))
    await asyncio.wait_for(first_running.wait(), 2)
    bot["version"] = "v2"
    bot["agent"]["instructions"] = "instructions-v2"
    second = await client.post("/api/bots/demo/run", json=payload, headers={"Accept": "text/event-stream"})
    release_first.set()
    first_response = await first
    for response, version in [(first_response, "v1"), (second, "v2")]:
        assert (
            "".join(event.delta for event in events(response) if event.type == EventType.TEXT_MESSAGE_CONTENT) == f"instructions-{version}"
        )
    await asyncio.to_thread(app.state.langfuse.flush)
    request_spans = [span for span in collector.get_finished_spans() if span.name == "agent_request"]
    assert {span.attributes["bot_version"] for span in request_spans} == {"v1", "v2"}


async def test_disconnect_closes_native_stream(
    client: httpx.AsyncClient,
    payload: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from muchabo import agent
    from muchabo.app import app

    first_chunk = asyncio.Event()
    cleaned = asyncio.Event()
    delivered = False

    async def slow(messages: list[ModelMessage], info: AgentInfo) -> AsyncGenerator[str]:
        try:
            yield "first"
            await asyncio.sleep(60)
        finally:
            cleaned.set()

    monkeypatch.setattr(agent, "OpenAIChatModel", lambda *args, **kwargs: FunctionModel(stream_function=slow))

    async def receive() -> dict[str, Any]:
        nonlocal delivered
        if not delivered:
            delivered = True
            return {"type": "http.request", "body": json.dumps(payload).encode(), "more_body": False}
        await first_chunk.wait()
        return {"type": "http.disconnect"}

    async def send(message: Message) -> None:
        if message["type"] == "http.response.body" and b"TEXT_MESSAGE_CONTENT" in message.get("body", b""):
            first_chunk.set()

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/bots/demo/run",
        "raw_path": b"/api/bots/demo/run",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json"), (b"accept", b"text/event-stream")],
        "server": ("test", 80),
        "client": ("127.0.0.1", 1234),
        "root_path": "",
    }
    await asyncio.wait_for(app(scope, receive, send), 2)
    await asyncio.wait_for(cleaned.wait(), 2)
    assert app.state.active_streams == 0
    assert app.state.streams_drained.is_set()
