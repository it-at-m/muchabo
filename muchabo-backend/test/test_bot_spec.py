"""Shared schema/native parsing parity and authenticated admin-read contracts."""

import asyncio
import json
from typing import Any
from uuid import uuid4

import httpx
import pytest
from conftest import CONTRACT_DIR
from jsonschema import Draft202012Validator
from pydantic import ValidationError
from pydantic_ai import AgentSpec


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", 1),
        ("schema_version", True),
        ("schema_version", "2"),
        ("schema_version", None),
        ("bot_id", "Bad"),
        ("bot_id", ""),
        ("bot_id", "a" * 65),
        ("version", None),
        ("version", 1),
        ("version", "v!"),
        ("version", "v\n"),
        ("access_policy", None),
        ("access_policy", "public"),
        ("extra", "secret"),
        ("agent", None),
    ],
)
def test_envelope_schema_parity(bot: dict[str, Any], field: str, value: object) -> None:
    from muchabo.bot_spec import BotSpec

    bot[field] = value
    schema = json.loads((CONTRACT_DIR / "bot-spec.schema.json").read_text(encoding="utf-8"))
    assert not Draft202012Validator(schema).is_valid(bot)
    with pytest.raises(ValidationError):
        BotSpec.model_validate(bot)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("model", ""),
        ("model", " \t\n"),
        ("model", "a" * 129),
        ("model", 42),
        ("model", None),
        ("instructions", ""),
        ("instructions", " \n"),
        ("instructions", "x" * 16001),
        ("instructions", []),
        ("instructions", None),
        ("instructions", "hi {{ user }}"),
        ("instructions", "hi }}"),
        ("name", None),
        ("name", "Bad"),
        ("capabilities", []),
        ("metadata", {}),
        ("model_settings", {}),
        ("retries", 1),
        ("output_schema", {}),
        ("deps_schema", {}),
        ("$schema", "https://example.com/schema"),
    ],
)
def test_native_subset_rejects_unsupported_data(bot: dict[str, Any], field: str, value: object) -> None:
    from muchabo.bot_spec import BotSpec

    bot["agent"][field] = value
    schema = json.loads((CONTRACT_DIR / "bot-spec.schema.json").read_text(encoding="utf-8"))
    assert not Draft202012Validator(schema).is_valid(bot)
    with pytest.raises(ValidationError):
        BotSpec.model_validate(bot)


def test_valid_boundary_and_cross_field_rules(bot: dict[str, Any]) -> None:
    from muchabo.bot_spec import BotSpec

    assert isinstance(BotSpec.model_validate(bot).agent, AgentSpec)
    bot["agent"].pop("name")
    bot["agent"]["model"] = "a" * 128
    bot["agent"]["instructions"] = "a" * 16000
    bot["version"] = "v" * 64
    assert BotSpec.model_validate(bot).version == bot["version"]
    bot["agent"]["name"] = "other"
    with pytest.raises(ValidationError):
        BotSpec.model_validate(bot)
    bot["agent"].pop("name")
    with pytest.raises(ValidationError):
        BotSpec.model_validate(bot, context={"bot_id": "other"})


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (404, "BOT_UNAVAILABLE"),
        (401, "CONFIGURATION_UNAVAILABLE"),
        (403, "CONFIGURATION_UNAVAILABLE"),
        (302, "CONFIGURATION_UNAVAILABLE"),
        (500, "CONFIGURATION_UNAVAILABLE"),
    ],
)
async def test_admin_failure_mapping(status: int, expected: str) -> None:
    from muchabo.bot_spec import PublicError, fetch_bot

    calls: list[httpx.Request] = []
    request_id = str(uuid4())

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.url == "http://localhost:8086/api/v1/bots/demo/spec"
        assert request.headers["authorization"] == "Bearer test-token"
        assert request.headers["x-request-id"] == request_id
        return httpx.Response(status, text="producer-secret", headers={"Location": "https://example.com"})

    async with httpx.AsyncClient(base_url="http://localhost:8086", transport=httpx.MockTransport(respond)) as client:
        with pytest.raises(PublicError) as error:
            await fetch_bot(client, "demo", "test-token", request_id)
    assert error.value.code == expected
    assert "producer-secret" not in str(error.value)
    assert len(calls) == 1


@pytest.mark.parametrize("response_kind", ["bad-json", "deep-json", "wrong-type", "oversized", "mismatch", "unknown", "missing"])
async def test_invalid_producer_response(bot: dict[str, Any], response_kind: str) -> None:
    from muchabo.bot_spec import PublicError, fetch_bot

    if response_kind == "mismatch":
        bot["bot_id"] = "other"
    if response_kind == "unknown":
        bot["secret"] = "producer-secret"
    if response_kind == "missing":
        del bot["agent"]["model"]
    content = json.dumps(bot).encode()
    if response_kind == "bad-json":
        content = b"producer-secret"
    if response_kind == "deep-json":
        content = b"[" * 2000 + b"0" + b"]" * 2000
    if response_kind == "oversized":
        content = b" " * 65537
    headers = {"Content-Type": "text/plain" if response_kind == "wrong-type" else "application/json"}
    async with httpx.AsyncClient(
        base_url="http://localhost",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, content=content, headers=headers),
        ),
    ) as client:
        with pytest.raises(PublicError) as error:
            await fetch_bot(client, "demo", "test-token", str(uuid4()))
    assert error.value.code == "INVALID_CONFIGURATION"


async def test_total_admin_deadline() -> None:
    from muchabo.bot_spec import PublicError, fetch_bot

    async def delayed(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(6)
        return httpx.Response(200, json={})

    start = asyncio.get_running_loop().time()
    async with httpx.AsyncClient(base_url="http://localhost", transport=httpx.MockTransport(delayed)) as client:
        with pytest.raises(PublicError) as error:
            await fetch_bot(client, "demo", "token", str(uuid4()))
    assert error.value.code == "CONFIGURATION_UNAVAILABLE"
    assert 4.9 <= asyncio.get_running_loop().time() - start < 5.8


async def test_fetch_refreshes_without_cache(bot: dict[str, Any]) -> None:
    from muchabo.bot_spec import fetch_bot

    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        bot["version"] = f"v{calls}"
        return httpx.Response(200, json=bot)

    async with httpx.AsyncClient(base_url="http://localhost", transport=httpx.MockTransport(respond)) as client:
        first = await fetch_bot(client, "demo", "token", str(uuid4()))
        second = await fetch_bot(client, "demo", "token", str(uuid4()))
    assert first.version == "v1"
    assert second.version == "v2"
    assert calls == 2


def test_exported_schemas_and_shared_fixture_corpus(bot: dict[str, Any]) -> None:
    from muchabo.bot_spec import BotSpec

    published = json.loads((CONTRACT_DIR / "bot-spec.schema.json").read_text(encoding="utf-8"))
    expected = BotSpec.model_json_schema()
    expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    assert published == expected
    native = json.loads((CONTRACT_DIR / "native-agent-spec.schema.json").read_text(encoding="utf-8"))
    expected_native = AgentSpec.model_json_schema_with_capabilities()
    expected_native["$schema"] = expected["$schema"]
    assert native == expected_native
    Draft202012Validator.check_schema(published)
    Draft202012Validator.check_schema(native)
    Draft202012Validator(native).validate(bot["agent"])
    invalid = json.loads((CONTRACT_DIR / "fixtures/invalid-bot-specs.json").read_text(encoding="utf-8"))
    design = json.loads(
        (CONTRACT_DIR.parents[1] / "specs/001-core-agent-backend/contracts/bot-spec.schema.json").read_text(encoding="utf-8")
    )
    for candidate in [bot, *invalid]:
        accepted: list[bool] = []
        for schema in [published, design]:
            # Both schema consumers must supplement portable structural validation with these cross-field checks.
            matches = candidate.get("bot_id") == "demo" and candidate["agent"].get("name", "demo") == candidate.get("bot_id")
            accepted.append(Draft202012Validator(schema).is_valid(candidate) and matches)
        try:
            BotSpec.model_validate(candidate, context={"bot_id": "demo"})
            accepted.append(True)
        except ValidationError:
            accepted.append(False)
        assert len(set(accepted)) == 1
