"""Integrated exported-span/log sentinel and teardown checks."""

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any

import httpx
import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.function import AgentInfo, FunctionModel


@pytest.mark.parametrize("failed", [False, True])
async def test_integrated_privacy_and_correlation(
    client: httpx.AsyncClient,
    payload: dict[str, Any],
    bot: dict[str, Any],
    collector: InMemorySpanExporter,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    failed: bool,
) -> None:
    from muchabo import agent
    from muchabo.app import app
    from muchabo.telemetry import ALLOWED_ATTRIBUTES

    payload["messages"][0]["content"] = "distinct-caller-personal-secret"
    bot["agent"]["instructions"] = "distinct-instruction-personal-secret"

    async def controlled(messages: list[ModelMessage], info: AgentInfo) -> AsyncGenerator[str]:
        if failed:
            raise RuntimeError("distinct-exception-personal-secret")
        yield "distinct-reply-personal-secret"

    monkeypatch.setattr(
        agent, "OpenAIChatModel", lambda *args, **kwargs: FunctionModel(stream_function=controlled, model_name="public-chat")
    )
    response = await client.post("/api/bots/demo/run", json=payload, headers={"Accept": "text/event-stream"})
    await asyncio.to_thread(app.state.langfuse.flush)
    spans = collector.get_finished_spans()
    assert spans
    serialized = json.dumps([json.loads(span.to_json()) for span in spans]) + caplog.text
    for sentinel in [
        "distinct-caller",
        "distinct-instruction",
        "distinct-exception",
        "distinct-reply",
        "test-admin-secret",
        "test-gateway-secret",
        "test-tracing-secret",
    ]:
        assert sentinel not in serialized
    assert response.headers["x-request-id"] in serialized
    assert payload["threadId"] in serialized
    assert "demo" in serialized and "v1" in serialized
    if not failed:
        usage_spans = [span for span in spans if "gen_ai.usage.input_tokens" in (span.attributes or {})]
        assert usage_spans
        for span in usage_spans:
            assert span.attributes is not None
            input_tokens = span.attributes["gen_ai.usage.input_tokens"]
            assert isinstance(input_tokens, int) and input_tokens >= 0
        assert "gen_ai.usage.output_tokens" in serialized
    for span in spans:
        assert set(span.attributes or {}) <= ALLOWED_ATTRIBUTES
        assert not span.events
        assert not span.status.description
    assert ("RUN_FAILED" if failed else "RUN_FINISHED") in caplog.text
