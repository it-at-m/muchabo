"""Controlled admin, native model and telemetry fixtures with no external I/O."""

import copy
import functools
import json
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
import pytest
from langfuse import Langfuse
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pydantic_ai import models
from pydantic_ai.models.test import TestModel

CONTRACT_DIR = Path(__file__).resolve().parents[2] / "contracts" / "bot-spec"
models.ALLOW_MODEL_REQUESTS = False


@pytest.fixture(autouse=True)
def environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Install test-only credentials before importing the application."""
    values = {
        "MUCHABO_ADMIN_BASE_URL": "http://localhost:8086",
        "MUCHABO_ADMIN_ACCESS_TOKEN": "test-admin-secret",
        "MUCHABO_LITELLM_BASE_URL": "http://localhost:4000/v1",
        "MUCHABO_LITELLM_API_KEY": "test-gateway-secret",
        "LANGFUSE_BASE_URL": "http://localhost:3000",
        "LANGFUSE_PUBLIC_KEY": "test-public-" + str(uuid4()),
        "LANGFUSE_SECRET_KEY": "test-tracing-secret",
        "LANGFUSE_OBSERVE_DECORATOR_IO_CAPTURE_ENABLED": "false",
        "LANGFUSE_MEDIA_UPLOAD_ENABLED": "false",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def bot() -> dict[str, Any]:
    """Return an independent shared bot fixture."""
    return json.loads((CONTRACT_DIR / "fixtures/bot-spec.json").read_text(encoding="utf-8"))


@pytest.fixture
def payload() -> dict[str, Any]:
    """Return an independent shared native AG-UI request."""
    return json.loads((CONTRACT_DIR / "fixtures/agent-request.json").read_text(encoding="utf-8"))


@pytest.fixture
def collector(monkeypatch: pytest.MonkeyPatch) -> Iterator[InMemorySpanExporter]:
    """Use Langfuse's supported exporter injection to collect masked spans locally."""
    from muchabo import telemetry

    exporter = InMemorySpanExporter()
    monkeypatch.setattr(telemetry, "Langfuse", functools.partial(Langfuse, span_exporter=exporter))
    yield exporter


@pytest.fixture
def test_model() -> TestModel:
    """Provide an exact native controlled reply without a gateway call."""
    return TestModel(custom_output_text="Hello.")


@pytest.fixture
async def client(
    monkeypatch: pytest.MonkeyPatch,
    collector: InMemorySpanExporter,
    bot: dict[str, Any],
    test_model: TestModel,
) -> AsyncIterator[httpx.AsyncClient]:
    """Run the real application lifespan with authenticated admin substitution."""
    from muchabo import agent
    from muchabo import app as app_module

    requests: list[httpx.Request] = []

    def admin_response(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.headers["authorization"] == "Bearer test-admin-secret"
        return httpx.Response(200, json=copy.deepcopy(bot), headers={"Cache-Control": "no-store"})

    original_client = httpx.AsyncClient
    monkeypatch.setattr(app_module, "AsyncClient", functools.partial(original_client, transport=httpx.MockTransport(admin_response)))
    monkeypatch.setattr(agent, "OpenAIChatModel", lambda *args, **kwargs: test_model)
    async with app_module.app.router.lifespan_context(app_module.app):
        app_module.app.state.admin_requests = requests
        app_module.app.state.controlled_model = test_model
        async with original_client(transport=httpx.ASGITransport(app=app_module.app), base_url="http://test") as http_client:
            yield http_client
