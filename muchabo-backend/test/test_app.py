"""Startup, operational probe and resource-lifetime acceptance checks."""

import asyncio
import threading
from typing import Any

import pytest
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


def test_healthz(collector: InMemorySpanExporter) -> None:
    from muchabo.app import app

    with TestClient(app) as client:
        response = client.get("/api/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert client.get("/").json() == {"message": "muchabo backend is running"}
        assert not collector.get_finished_spans()
        admin = app.state.admin
        gateway = app.state.gateway
        assert gateway.max_retries == 0
        assert gateway.timeout == 20
    assert admin.is_closed
    assert gateway.is_closed()


@pytest.mark.parametrize(
    "name",
    [
        "MUCHABO_ADMIN_BASE_URL",
        "MUCHABO_ADMIN_ACCESS_TOKEN",
        "MUCHABO_LITELLM_BASE_URL",
        "MUCHABO_LITELLM_API_KEY",
        "LANGFUSE_BASE_URL",
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_OBSERVE_DECORATOR_IO_CAPTURE_ENABLED",
        "LANGFUSE_MEDIA_UPLOAD_ENABLED",
    ],
)
def test_each_required_setting_fails_startup(
    name: str,
    monkeypatch: pytest.MonkeyPatch,
    collector: InMemorySpanExporter,
) -> None:
    from muchabo.app import app

    monkeypatch.delenv(name)
    with pytest.raises(ValueError, match="Missing or invalid runtime settings") as error:
        with TestClient(app):
            pytest.fail("Invalid startup settings were accepted")
    assert "test-admin-secret" not in str(error.value)
    assert "test-tracing-secret" not in str(error.value)
    assert not collector.get_finished_spans()


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("MUCHABO_ADMIN_BASE_URL", "http://private-production.example"),
        ("MUCHABO_ADMIN_BASE_URL", "https://host.example/path"),
        ("MUCHABO_LITELLM_BASE_URL", "https://user:distinct-url-secret@host.example/v1"),
        ("LANGFUSE_BASE_URL", "https://host.example?token=distinct-url-secret"),
        ("LANGFUSE_BASE_URL", "https://host.example:bad"),
        ("MUCHABO_LITELLM_API_KEY", "distinct-credential-secret\n"),
        ("MUCHABO_ADMIN_ACCESS_TOKEN", " "),
        ("LANGFUSE_OBSERVE_DECORATOR_IO_CAPTURE_ENABLED", "true"),
        ("LANGFUSE_MEDIA_UPLOAD_ENABLED", "true"),
    ],
)
def test_invalid_settings_are_redacted(
    name: str,
    value: str,
    monkeypatch: pytest.MonkeyPatch,
    collector: InMemorySpanExporter,
) -> None:
    from muchabo.app import app
    from muchabo.settings import Settings
    from pydantic import ValidationError

    monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError) as validation:
        Settings()
    assert "distinct-" not in str(validation.value)
    with pytest.raises(ValueError) as startup:
        with TestClient(app):
            pytest.fail("Invalid startup settings were accepted")
    assert "distinct-" not in str(startup.value)


async def test_shutdown_waits_for_drain_and_runs_telemetry_off_loop(
    collector: InMemorySpanExporter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from muchabo.app import app, lifespan

    manager = lifespan(app)
    await manager.__aenter__()
    admin = app.state.admin
    gateway = app.state.gateway
    calls: list[tuple[str, int]] = []
    for name, owner in [("flush", app.state.langfuse), ("shutdown", app.state.langfuse), ("shutdown", app.state.provider)]:
        original = getattr(owner, name)

        def track(*args: Any, _name: str = name, _original: Any = original, **kwargs: Any) -> Any:
            calls.append((_name, threading.get_ident()))
            return _original(*args, **kwargs)

        monkeypatch.setattr(owner, name, track)
    app.state.streams_drained.clear()
    closing = asyncio.create_task(manager.__aexit__(None, None, None))
    await asyncio.sleep(0.02)
    assert not closing.done()
    assert not admin.is_closed and not gateway.is_closed()
    app.state.streams_drained.set()
    await asyncio.wait_for(closing, 2)
    assert admin.is_closed and gateway.is_closed()
    assert [name for name, thread in calls][:2] == ["flush", "shutdown"]
    assert all(thread != threading.get_ident() for name, thread in calls)
