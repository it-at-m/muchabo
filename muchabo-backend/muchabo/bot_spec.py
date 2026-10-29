"""Strict native-spec boundary and bounded authenticated admin reads."""

import asyncio
import json
from pathlib import Path
from typing import Annotated, Any, Literal, Self

import httpx
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    StringConstraints,
    TypeAdapter,
    ValidationError,
    ValidationInfo,
    WithJsonSchema,
    model_validator,
)
from pydantic_ai import AgentSpec

BODY_LIMIT = 64 * 1024
CONFIG_TIMEOUT = 5
IDENTIFIER_SCHEMA = {
    "type": "string",
    "minLength": 1,
    "maxLength": 64,
    "pattern": r"^[a-z0-9][a-z0-9_-]*$",
    "not": {"pattern": "[^a-z0-9_-]"},
}
# JSON Schema engines may let `$` match before a trailing newline; forbid every non-identifier character explicitly.
Identifier = Annotated[
    str, StringConstraints(strict=True, min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$"), WithJsonSchema(IDENTIFIER_SCHEMA)
]
identifier_adapter = TypeAdapter(Identifier)
model_adapter = TypeAdapter(Annotated[str, StringConstraints(strict=True, min_length=1, max_length=128, pattern=r"\S")])
instructions_adapter = TypeAdapter(Annotated[str, StringConstraints(strict=True, min_length=1, max_length=16000, pattern=r"\S")])
AGENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["model", "instructions"],
    "properties": {
        "model": model_adapter.json_schema(),
        "instructions": {
            "type": "string",
            "minLength": 1,
            "maxLength": 16000,
            "allOf": [{"pattern": r"\S"}, {"not": {"pattern": r"\{\{"}}, {"not": {"pattern": r"\}\}"}}],
        },
        "name": identifier_adapter.json_schema(),
    },
}


class PublicError(Exception):
    """Fixed public HTTP error; never contains producer or validator details."""

    def __init__(self, code: Literal["BOT_UNAVAILABLE", "INVALID_CONFIGURATION", "CONFIGURATION_UNAVAILABLE"]) -> None:
        self.code = code
        self.status, self.message = {
            "BOT_UNAVAILABLE": (404, "This bot is not available."),
            "INVALID_CONFIGURATION": (502, "The bot configuration is invalid."),
            "CONFIGURATION_UNAVAILABLE": (503, "The bot configuration is temporarily unavailable. Please try again."),
        }[code]
        super().__init__(self.message)


def validate_agent(value: object) -> AgentSpec:
    """Validate raw supported keys/types before native AgentSpec can discard them."""
    if not isinstance(value, dict) or set(value) - {"model", "instructions", "name"} or not {"model", "instructions"} <= set(value):
        raise ValueError("Unsupported native agent specification")
    model_adapter.validate_python(value["model"])
    instructions = instructions_adapter.validate_python(value["instructions"])
    if "{{" in instructions or "}}" in instructions:
        raise ValueError("Template instructions are unsupported")
    if "name" in value:
        identifier_adapter.validate_python(value["name"])
    return AgentSpec.model_validate(value)


class BotSpec(BaseModel):
    """Versioned platform envelope containing the native AgentSpec."""

    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)
    schema_version: Literal["1"]
    bot_id: Identifier
    version: Identifier
    access_policy: Literal["anonymous", "authenticated"]
    agent: Annotated[AgentSpec, BeforeValidator(validate_agent), WithJsonSchema(AGENT_SCHEMA)]

    @model_validator(mode="after")
    def validate_identity(self, info: ValidationInfo) -> Self:
        """Enforce cross-field and requested-path identity outside portable JSON Schema."""
        if self.agent.name is not None and self.agent.name != self.bot_id:
            raise ValueError("Agent identity does not match bot identity")
        if info.context and self.bot_id != info.context["bot_id"]:
            raise ValueError("Bot identity does not match requested path")
        return self


async def fetch_bot(client: httpx.AsyncClient, bot_id: str, token: str, request_id: str) -> BotSpec:
    """Fetch one current definition with no cache, retry or redirect, within five seconds."""
    try:
        async with asyncio.timeout(CONFIG_TIMEOUT):
            async with client.stream(
                "GET",
                f"/api/v1/bots/{bot_id}/spec",
                follow_redirects=False,
                headers={"Authorization": f"Bearer {token}", "X-Request-ID": request_id, "Accept": "application/json"},
            ) as response:
                if response.status_code == 404:
                    raise PublicError("BOT_UNAVAILABLE")
                if response.status_code != 200:
                    raise PublicError("CONFIGURATION_UNAVAILABLE")
                if response.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
                    raise PublicError("INVALID_CONFIGURATION")
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    if len(body) + len(chunk) > BODY_LIMIT:
                        raise PublicError("INVALID_CONFIGURATION")
                    body.extend(chunk)
                return BotSpec.model_validate(json.loads(body), context={"bot_id": bot_id})
    except TimeoutError, httpx.HTTPError:
        raise PublicError("CONFIGURATION_UNAVAILABLE") from None
    except ValidationError, ValueError, UnicodeDecodeError, RecursionError:
        raise PublicError("INVALID_CONFIGURATION") from None


def export_schemas(destination: Path) -> None:
    """Regenerate bundled native and supported schemas from the installed pinned library."""
    schemas: dict[str, dict[str, Any]] = {
        "native-agent-spec.schema.json": AgentSpec.model_json_schema_with_capabilities(),
        "bot-spec.schema.json": BotSpec.model_json_schema(),
    }
    for name, schema in schemas.items():
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        (destination / name).write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    export_schemas(Path(__file__).resolve().parents[2] / "contracts" / "bot-spec")
