# muchabo backend

One stateless FastAPI runtime serving configured anonymous agents through native
Pydantic AI 2.63.0 and AG-UI 1.0.0. Each request loads a versioned bot definition
from the admin backend and uses the configured LiteLLM gateway. No production bot
is hardcoded and no conversation is retained between requests.

## Install, check and start

Use stable Python 3.14.4 and uv. From this directory:

```bash
uv sync --frozen --group dev
uv run --frozen pytest
uv run --frozen ruff check --config ../ruff.toml .
uv run --frozen ruff format --check --config ../ruff.toml .
uv run --frozen ty check
uv run --frozen python main.py
```

Automated checks use authenticated admin substitutes, native TestModel/FunctionModel
and a local Langfuse span exporter; no live model or telemetry calls are needed.

## Required configuration

Supply the following through the process environment or an uncommitted local `.env`:

| Variable | Purpose |
|----------|---------|
| `MUCHABO_ADMIN_BASE_URL` | Admin origin, e.g. `http://localhost:8086`; no path/query/userinfo. |
| `MUCHABO_ADMIN_ACCESS_TOKEN` | Externally provisioned read-only JWT service credential. |
| `MUCHABO_LITELLM_BASE_URL` | Gateway API base, e.g. `http://localhost:4000/v1`. |
| `MUCHABO_LITELLM_API_KEY` | Gateway credential. |
| `LANGFUSE_BASE_URL` | Tracing destination. |
| `LANGFUSE_PUBLIC_KEY` | Langfuse project public credential. |
| `LANGFUSE_SECRET_KEY` | Langfuse project secret credential. |
| `LANGFUSE_OBSERVE_DECORATOR_IO_CAPTURE_ENABLED` | Required `false`. |
| `LANGFUSE_MEDIA_UPLOAD_ENABLED` | Required `false`. |

`MUCHABO_APP_NAME` and `MUCHABO_LOG_LEVEL` retain optional application-name and log-level
settings. HTTPS is required except loopback HTTP for local validation. Invalid or
missing settings fail at startup with field names only; credential values are not
included. Content and media capture remain disabled even when settings come from `.env`.

Live use requires an admin implementation of the
[spec-read contract](../specs/001-core-agent-backend/contracts/bot-spec-api.md), a dedicated
JWT spec-reader token with the correct issuer/audience, a gateway alias matching the
bot configuration, and the Langfuse project. Provision/renew service tokens externally.
Configuration bodies and credentials are never caller permissions.

## Send one interaction

From repository root, after the configuration owner activates the example `demo`
definition through its schema and evaluation gates:

```bash
curl --fail-with-body http://localhost:8080/api/healthz
curl --no-buffer --fail-with-body \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  --data-binary @contracts/bot-spec/fixtures/agent-request.json \
  http://localhost:8080/api/bots/demo/run
```

Health returns `{"status":"ok"}` without a configuration or model call. Agent success
streams native assistant text and exactly one `RUN_FINISHED`; execution failure
streams one fixed `RUN_ERROR` with `RUN_FAILED` or `RUN_TIMEOUT` and no later success.
`X-Request-ID` is server-generated and correlates the response with diagnostics.
Replies depend on the configured gateway/model; exact example wording is test-only.

The [runtime contract](../specs/001-core-agent-backend/contracts/agent-runtime.md)
defines the strict one-message/UUID/empty-state request scope and all fixed public
HTTP errors: 403/404/406/413/415/422/502/503. Both request and admin response bodies
are limited to 64 KiB. Invalid inputs/configurations and authenticated bot definitions
are rejected before model execution. Incoming identity/role headers confer no access.

Fixed limits: admin fetch **5 seconds total**, gateway HTTP attempt **20 seconds**,
native model request **25 seconds**, agent run **30 seconds**. Admin, SDK and agent
retries are all zero; no redirects, configuration cache or fallback bot exists.

## Core responsibilities

| Location | Responsibility | Requirement |
|----------|----------------|-------------|
| `muchabo/settings.py` | Validate external runtime settings and redact startup errors. | FR-002/007 |
| `muchabo/bot_spec.py` | Strict native AgentSpec boundary and per-request admin configuration read. | FR-002/003 |
| `muchabo/agent.py` — `CallerContext` | Fresh server-set anonymous/public identity, no user or roles. | FR-004/005 |
| `muchabo/agent.py` — `reply` | Direct native Agent execution and bounded model access. | FR-001/006 |
| `muchabo/app.py`, `muchabo/agent.py` | HTTP validation and native AG-UI reply delivery/terminal sanitization. | FR-001/002/006 |
| `muchabo/telemetry.py` | Native owned tracing, opaque correlation, fixed allowlisted diagnostics and teardown. | FR-008 |

Later concrete features extend native library capabilities through coordinated
contract changes. This core adds no tools, persistence, registry, service wrapper,
approvals or handover mechanisms. Native reported token usage is retained; Langfuse
can price configured model aliases when matching project model prices exist. Missing
usage/cost is not reconstructed from content.

Shutdown drains active streams, closes HTTP clients, flushes/shuts down Langfuse off
the event loop, and explicitly shuts down the owned provider. There is no per-request
flush. Disconnects cancel/close native execution. Uvicorn access logging is disabled
so caller IPs and raw request URLs are not emitted alongside the fixed diagnostics.

## Container and upgrades

Build from repository root so trusted public schemas are packaged:

```bash
docker build -f muchabo-backend/Dockerfile -t muchabo-backend:local .
docker compose up --build backend
```

With Podman, use the same root context and Dockerfile:

```bash
podman build -f muchabo-backend/Dockerfile -t localhost/muchabo-backend:local .
podman compose up --build backend
```

The image scopes inputs to the backend and `contracts/bot-spec/`; `.dockerignore`
excludes local environments, credentials and unrelated components. It retains the
non-root user, `main.py`, and port 8080, executing through frozen uv per constitution 2.1.1.

For upgrades, update exact direct pins with uv, regenerate `uv.lock`, verify
`uv sync --frozen --group dev`, then run from this directory:

```bash
uv run --frozen -m muchabo.bot_spec
uv run --frozen pytest
uv run --frozen ruff check --config ../ruff.toml .
uv run --frozen ruff format --check --config ../ruff.toml .
uv run --frozen ty check
```

Review generated native/supported schemas and fixtures with both contract consumers;
resolve references locally only. Producer contract tests, frontend native AG-UI
conformance and passing bot/model regression evidence are required before activation.
See [validation evidence and live prerequisites](../specs/001-core-agent-backend/quickstart.md).
Direct agent/tracing additions use MIT (Pydantic AI, Pydantic, Langfuse, AG-UI) and
Apache-2.0 (OpenAI SDK, OpenTelemetry SDK). Preserve applicable copyright/license
notices when redistributing; review transitive distribution notices when upgrading.
The project remains MIT licensed.
