"""Owned native tracing lifecycle and content-free structured diagnostics."""

import asyncio
import json
import logging
import os
from typing import Literal

from langfuse import Langfuse
from langfuse.types import MaskOtelSpansParams, MaskOtelSpansResult, OtelSpanPatch
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanLimits, TracerProvider
from pydantic_ai.models.instrumented import InstrumentationSettings

from .settings import Settings

DiagnosticCode = Literal[
    "RUN_FINISHED",
    "RUN_FAILED",
    "RUN_TIMEOUT",
    "RUN_CANCELLED",
    "BOT_UNAVAILABLE",
    "ACCESS_DENIED",
    "REQUEST_TOO_LARGE",
    "UNSUPPORTED_MEDIA_TYPE",
    "UNSUPPORTED_RESPONSE_TYPE",
    "INVALID_REQUEST",
    "INVALID_CONFIGURATION",
    "CONFIGURATION_UNAVAILABLE",
]
CORRELATION_FIELDS = frozenset({"request_id", "conversation_id", "session_id", "bot_id", "bot_version", "model_alias"})
ALLOWED_ATTRIBUTES = (
    frozenset(
        {
            "event_code",
            "duration_ms",
            "model_name",
            "gen_ai.request.model",
            "gen_ai.agent.name",
            "gen_ai.agent.call.id",
            "gen_ai.conversation.id",
            "gen_ai.operation.name",
            "gen_ai.usage.input_tokens",
            "gen_ai.usage.output_tokens",
            "gen_ai.usage.cache_read_tokens",
            "gen_ai.usage.cache_write_tokens",
            "gen_ai.aggregated_usage.input_tokens",
            "gen_ai.aggregated_usage.output_tokens",
            "gen_ai.aggregated_usage.cache_read_tokens",
            "gen_ai.aggregated_usage.cache_write_tokens",
            "langfuse.session.id",
            "langfuse.trace.name",
            "langfuse.version",
            "metadata",
        }
    )
    | CORRELATION_FIELDS
    | frozenset(prefix + key for prefix in ("langfuse.trace.metadata.", "langfuse.observation.metadata.") for key in CORRELATION_FIELDS)
)
logger = logging.getLogger("muchabo.runtime")


def mask_spans(*, params: MaskOtelSpansParams) -> MaskOtelSpansResult:
    """Drop non-allowlisted native attributes before the Langfuse exporter emits them."""
    return MaskOtelSpansResult(
        span_patches={
            identifier: OtelSpanPatch(delete_attributes=tuple(key for key in span.attributes if key not in ALLOWED_ATTRIBUTES))
            for identifier, span in params.spans.items()
        }
    )


def initialize(settings: Settings) -> tuple[Langfuse, TracerProvider, InstrumentationSettings]:
    """Initialize one owned provider and Langfuse's native exporting pipeline."""
    # pydantic-settings reads .env independently; ensure the native SDK sees the validated capture policy too.
    os.environ["LANGFUSE_OBSERVE_DECORATOR_IO_CAPTURE_ENABLED"] = "false"
    os.environ["LANGFUSE_MEDIA_UPLOAD_ENABLED"] = "false"
    # Native instrumentation suppresses exception content; event capture is unnecessary in this scope.
    provider = TracerProvider(resource=Resource({"service.name": "muchabo"}), span_limits=SpanLimits(max_events=0))
    client = Langfuse(
        public_key=settings.langfuse_public_key.get_secret_value(),
        secret_key=settings.langfuse_secret_key.get_secret_value(),
        base_url=settings.langfuse_base_url.get_secret_value(),
        tracer_provider=provider,
        mask_otel_spans=mask_spans,
        should_export_span=lambda span: (
            span.instrumentation_scope is not None and span.instrumentation_scope.name in {"muchabo.runtime", "pydantic-ai"}
        ),
    )
    instrumentation = InstrumentationSettings(
        tracer_provider=provider,
        include_content=False,
        include_binary_content=False,
        include_model_request_parameters=False,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logger.setLevel(settings.log_level)
    return client, provider, instrumentation


async def shutdown(client: Langfuse, provider: TracerProvider) -> None:
    """Flush and shut down workers off the event loop after all streams drain."""
    try:
        await asyncio.to_thread(client.flush)
    finally:
        try:
            await asyncio.to_thread(client.shutdown)
        finally:
            await asyncio.to_thread(provider.shutdown)


def diagnostic(code: DiagnosticCode, attributes: dict[str, str], duration_ms: float = 0) -> None:
    """Emit a fixed event code and only server-controlled correlation fields."""
    fields = {key: value for key, value in attributes.items() if key in CORRELATION_FIELDS}
    logger.info(json.dumps({"event_code": code, **fields, "duration_ms": duration_ms}, sort_keys=True))
