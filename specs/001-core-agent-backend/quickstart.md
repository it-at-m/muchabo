# Quickstart and Validation: Minimal Core Agent Backend

**Status**: Core runtime implemented; controlled acceptance checks pass. Live producer/frontend activation requires the prerequisites below.

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

## Implementation verification record

- Stable Python 3.14.4; frozen uv installation verified with all exact agent/tracing/SDK pins.
- User-installed supporting updates retained: pydantic-settings 2.16.2, pytest 9.2.0, ty 0.0.94; jsonschema 4.26.0 is dev-only.
- US1 focused suite: 92 passing checks in 10.81 seconds, including SC-001 ten exact replies, SC-004 ten concurrent isolated replies, and SC-005 in-flight v1/next-request v2 refresh without edits or redeployment.
- SC-003: invalid transport/input/configuration, access denial, admin failure/deadline, model failure, timeout, and disconnect checks passed; exported traces/logs contained none of the seeded content/credential sentinels.
- Timeout integration uses a shortened test-only deadline for native RunTimedOut/cancellation behavior; production limits remain fixed at 5/20/25/30 seconds. The actual five-second admin deadline was measured independently.
- Shared/native generated schemas and strict fixture parity passed, including explicit cross-field identity checks and trailing-newline rejection.
- These results use controlled admin/model/telemetry services. No live admin endpoint, frontend AG-UI conformance, Langfuse delivery, or bot activation/evaluation was claimed.
- Final backend suite: **116 passing tests in 8.93 seconds**, **97% runtime coverage**; frozen install, Ruff lint/format and ty checks passed. Final boundary checks also cover deeply nested malformed JSON without raw failures.
- SC-002: root-context Podman image performed a fresh frozen Linux installation on stable Python 3.14.4; a network-disabled container completed valid startup/health and an exact controlled first reply in 0.082 seconds after installation. This is automated controlled-service evidence, not a timed live maintainer deployment.
- Container packaging checks passed for UID 1001, both published schemas and fixture inputs, and absence of credential/test/unrelated component files. The original unavailable UBI tag was replaced by the verified UBI 10.1 multi-platform digest; user-management tooling and a non-root-readable managed interpreter location were fixed from actual build failures.
- SC-006: README maps configuration, caller context, execution and delivery to the four core responsibilities and current FR requirements; tracing/settings remain supporting current requirements. No speculative capability scaffolding was introduced.
- Final Podman rebuild and network-disabled non-root smoke passed: startup/reply 0.310 seconds and three exported native/request spans with the fixed allowlist. Native model usage is not duplicated on the owned request span. No live services were contacted by this smoke check.
- Four changed YAML configs parsed; six public JSON artifacts parsed with local-only schema references; 25 relative Markdown links resolved; git whitespace check passed. CI now uses frozen installation/execution and Ruff/ty gates; contract paths trigger runtime/admin change filters. Remote CI jobs and arm64 image execution were not run locally.
- The final image's actual frozen uv/main.py entrypoint started on port 8080, answered health with external networking disabled, and stopped gracefully. Uvicorn access logging is disabled; the health request emitted no caller IP/raw URL access record. The temporary validation container was removed.

## Container validation

From repository root (Podman is the local validation engine; Docker uses the same Dockerfile):

```bash
podman build -f muchabo-backend/Dockerfile -t localhost/muchabo-backend:local .
podman compose up --build backend
```

Compose requires its provider and the root uncommitted `.env`. For live curl validation,
provision the documented services and reader token; the network-disabled image smoke
check uses native model/admin/exporter substitutes instead.

For an upgrade, update exact dependency pins and `uv.lock` together, regenerate native schema exports, and run schema/AG-UI parity, unit, integration, and evaluation checks. Do not activate a changed bot/model until its regression suite passes. The Python container must build from the repository root so published shared contract artifacts are included; update compose/workflow build contexts with that change.
