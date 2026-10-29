# Quickstart and Validation: Minimal Core Agent Backend

**Status**: Guide for the planned implementation. The current scaffold does not yet serve the agent endpoint or contain the new tests.

## Prerequisites

- Python 3.14 and uv; install from the committed backend lockfile once implemented.
- For manual live validation: an admin service implementing the [bot-spec contract](contracts/bot-spec-api.md), a read-only JWT service token with the correct issuer/audience, a LiteLLM gateway with the `public-chat` alias, and Langfuse credentials/destination.
- Activate the [demo configuration](contracts/fixtures/bot-spec.json) through the configuration owner after its validation/evaluation gates pass. Do not create a production hardcoded runtime bot.
- Automated validation uses an authenticated-response admin substitute, Pydantic AI TestModel/FunctionModel, and an in-memory telemetry collector. It requires no live model, admin, or Langfuse calls.

## Install and verify

From `muchabo-backend/`:

```bash
uv sync --frozen --group dev
uv run --frozen pytest
uv run --frozen ruff check --config ../ruff.toml .
uv run --frozen ruff format --check --config ../ruff.toml .
uv run --frozen ty check
```

Expected: existing health checks and new core behavior/contract tests pass; no real model requests occur. The schema/fixture parity suite must cover strict types, unknown fields, unsupported native capabilities, and cross-field identity rules. No claims about live admin/frontend compatibility follow solely from consumer mocks.

## Configure live validation

Provide these settings through the backend's local uncommitted `.env` or deployment environment:

| Setting | Purpose |
|---------|---------|
| `MUCHABO_ADMIN_BASE_URL` | Admin origin, for example `http://localhost:8086`. |
| `MUCHABO_ADMIN_ACCESS_TOKEN` | Externally provisioned read-only JWT service token; secret. |
| `MUCHABO_LITELLM_BASE_URL` | Gateway API base including `/v1`, for example `http://localhost:4000/v1`. |
| `MUCHABO_LITELLM_API_KEY` | Gateway credential; secret. |
| `LANGFUSE_BASE_URL` | Tracing destination. |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | Project credentials; secret. |
| `LANGFUSE_OBSERVE_DECORATOR_IO_CAPTURE_ENABLED` | `false`. |
| `LANGFUSE_MEDIA_UPLOAD_ENABLED` | `false`. |

All required URLs/credentials must be validated during startup without displaying their values in errors. Public plain-HTTP origins are not production defaults; localhost HTTP is for local validation. Timeout/retry limits are fixed in this increment as documented in the [runtime contract](contracts/agent-runtime.md).

## Start and send one message

From `muchabo-backend/`:

```bash
uv run --frozen python main.py
```

In another terminal, from repository root:

```bash
curl --fail-with-body http://localhost:8080/api/healthz
curl --no-buffer --fail-with-body \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  --data-binary @specs/001-core-agent-backend/contracts/fixtures/agent-request.json \
  http://localhost:8080/api/bots/demo/run
```

Expected: health is `{"status":"ok"}`; chat sends native AG-UI assistant text and one `RUN_FINISHED`. `X-Request-ID` correlates the interaction with its trace. Complete setup and first reply within 10 minutes once prerequisites are available. Actual reply wording is controlled by the configured model; automated tests use exact controlled replies.

## Acceptance matrix

| Scenario | Action | Expected result |
|----------|--------|-----------------|
| Successful serving | Run ten valid interactions against a controlled model. | Ten expected replies and ten successful terminal events. |
| Invalid request | Test empty/whitespace text, multiple messages, multimodal input, nonempty tools/state/context, and malformed IDs. | Sanitized `422`; zero model calls. |
| Configuration validation | Supply invalid version, unknown native fields, template instructions, or mismatched bot ID/name. | Sanitized `502`; zero model calls. |
| Access denial | Return valid `authenticated` configuration. | `403 ACCESS_DENIED`; zero model calls; no employee privileges inferred from headers/body. |
| Config unavailable | Fail admin access or delay response past 5 seconds. | Sanitized `503`; no fallback agent. |
| Model unavailable | Controlled model raises an exception containing a distinctive test secret. | One `RUN_ERROR/RUN_FAILED`; test secret absent from HTTP, events, logs, and traces. |
| Timeout | Controlled model exceeds the configured run deadline. | One `RUN_ERROR/RUN_TIMEOUT`; no later `RUN_FINISHED`. |
| Isolation | Run ten concurrent interactions with distinct identifiers/content. | Zero message/context leakage; all streams cleaned up. |
| Config refresh | Publish `v2` with changed literal instructions and repeat request. | Next request uses `v2`; in-flight `v1` remains attributed to `v1`; no runtime edit/redeploy. |
| Disconnect | Close a client stream during execution. | Native iterator cancelled/closed; no retained request state. |
| Observability | Inspect controlled success/failure spans and one live Langfuse run. | Bot/version and opaque correlation present; reported tokens/cost available; no personal content or credentials. |
| Simplicity | Review documented configuration/context/execution/reply responsibilities. | Each maps to a current requirement; no hypothetical extension framework. |

Producer-side bot-spec schema checks and frontend-side AG-UI conformance must pass before live integration. They are separate component prerequisites, not implemented UI or configuration administration in this core feature.

## Shutdown and upgrades

Stop the service gracefully. Drain active streams, close HTTP clients, flush/shut down Langfuse off the event loop, and shut down the owned OTEL provider. Do not flush telemetry on every request.

For an upgrade, update exact dependency pins and `uv.lock` together, regenerate native schema exports, and run schema/AG-UI parity, unit, integration, and evaluation checks. Do not activate a changed bot/model until its regression suite passes. The Python container must build from the repository root so published shared contract artifacts are included; update compose/workflow build contexts with that change.
