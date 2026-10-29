# Implementation Plan: Minimal Core Agent Backend

**Branch**: `chore/init-speckit-constitution` | **Date**: 2026-10-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-core-agent-backend/spec.md`

**Status**: Implementation complete; frozen checks and Podman container validation passed. See [quickstart evidence](quickstart.md).

**Feature identifier**: `001-core-agent-backend`. The setup script reports this identifier as `BRANCH`; Git confirms the actual branch shown above. Feature paths are resolved independently through `.specify/feature.json`.

## Summary

Establish the smallest shared agent-serving runtime in the existing FastAPI backend. Use Pydantic AI's agent execution, declarative agent specs, and built-in AG-UI adapter directly. Resolve a versioned bot spec from the admin backend per request and call the LiteLLM gateway. Keep execution context request-local and extend through existing library capabilities only when a later feature needs them.

Research verified stable Pydantic AI v2 and Python 3.14 support. Constitution 2.1.0 permits the compatible, locked upstream dependencies required by stable Langfuse. Phase 1 defines the native agent-spec subset, anonymous caller context, admin HTTP contract, AG-UI terminal behavior, and validation guide. Admin producer implementation, service credential provisioning, and frontend integration remain external prerequisites; controlled substitutes enable complete core-runtime verification.

## Technical Context

**Language/Version**: Python 3.14; existing manifest requires `>=3.14`.

**Primary Dependencies**: Preserve FastAPI `0.162.0`, httpx `0.28.1`, pydantic-settings `2.16.1`, and Uvicorn `0.54.0`. Add `pydantic-ai-slim[openai,ag-ui,spec]==2.63.0` and `langfuse==5.0.4`. Explicitly pin directly imported `pydantic==2.14.1`, `openai==3.31.0`, `ag-ui-protocol==1.0.0`, and `opentelemetry-sdk==1.45.1`. The SDK/protocol packages already belong to the framework/tracing dependency graph; explicit pins declare direct API use. No LiteLLM runtime package or generic schema-validation wrapper. Resolve the complete compatible graph with uv during implementation and commit `uv.lock`; no dependency was installed by planning.

**Storage**: No runtime database or in-process conversation persistence. Bot configurations remain externally owned; no cross-request history or approval state is introduced.

**Testing**: Existing pytest `9.1.1`, pytest-asyncio `1.4.1`, pytest-cov `7.1.0`, Ruff `0.17.3`, and ty `0.0.92`. Use Pydantic AI TestModel/FunctionModel and disable real model requests. Contract verification must cover both sides of the bot-spec and AG-UI boundaries before activation.

**Target Platform**: Existing Linux container and local Python development; preserve `main.py` startup on port 8080.

**Project Type**: Asynchronous web service within the existing four-component platform.

**Performance Goals**: Ten controlled successful interactions, ten isolated simultaneous interactions, and first successful interaction within ten minutes after prerequisites are available. No production throughput or uptime target is added.

**Constraints**: No custom agent loop, library wrappers, single-implementation abstractions, plugin framework, or hypothetical capability scaffolding. Explicit timeouts and bounded retries; no personal content in tracing; secrets in runtime configuration. Dependency changes must update exact manifest pins and a committed lockfile together.

**Scale/Scope**: One configured agent per request; one message/reply per interaction. Configuration administration, tools, retrieval, approvals, handover, and persistent conversation management remain later features.

### Minimal execution design

1. The existing application lifespan validates required settings, opens one admin httpx client and one AsyncOpenAI gateway client, and initializes an owned OTEL provider with Langfuse. Set SDK `max_retries=0` and `timeout=20`; native run settings enforce `request_timeout=25`, `timeout=30`, and agent retries zero.
2. `POST /api/bots/{bot_id}/run` parses native AG-UI input and applies the single-message, 64-KiB body, and empty tools/state/context restrictions before execution. Return fixed public validation errors, never raw validator inputs.
3. Fetch `GET /api/v1/bots/{bot_id}/spec` through authenticated admin HTTP with a 5-second total deadline, no retry/redirect/cache, and 64-KiB response limit. Validate the strict platform envelope and its supported native AgentSpec fields. Fail closed for mismatched identifiers, unsupported features, or unavailable configuration.
4. Allow only explicit `anonymous` configurations. Build a fresh typed context with no user identity, tenant `public`, and empty roles. Service credentials do not enter caller context. Authenticated/internal bots are denied; no employee-authentication feature is added.
5. Create one native Agent from the fetched spec, supplying an explicit OpenAIChatModel and LiteLLMProvider using the configured AsyncOpenAI client. Model prefixes cannot reroute requests. Add only native Instrumentation capability with content/binary/model-request-parameter capture disabled; names and metadata come from the fixed non-personal allowlist.
6. Use AGUIAdapter.from_request/run_stream/streaming_response; pass per-run deps, UUID run ID, and correlation metadata. A small typed terminal-event sanitizer is necessary for fixed public errors and timeout semantics; retain native event transformation/encoding. Keep agent, correlation, and request resources open inside the consuming iterator until streaming completes.
7. At shutdown, drain streams, close application-owned HTTP clients, flush/shut down Langfuse with `asyncio.to_thread`, and explicitly shut down the owned OTEL provider. No per-request telemetry flush or retained conversations.

Document fixed bounds and all required URLs/secrets in the backend README. Export shared schema/fixtures as public contract resources; keep the bot config owner and frontend on their documented boundaries.

## Constitution Check

*GATE: Must pass before committing to design. Re-check after Phase 1 design.*

| Gate | Result | Evidence / required action |
|------|--------|----------------------------|
| I. Simplicity first | PASS (design) | Direct native execution/adapter; focused boundary validation and error filtering, no speculative framework. |
| II. Config over code | PASS (design) | Native AgentSpec subset in a strict shared envelope; per-request admin fetch and immutable version. Producer conformance required before live activation. |
| III. Stateless asynchronous runtime | PASS (design) | Async clients, native streaming, request-local agent/context, no cached conversation state. |
| IV. Security and data protection | PASS (design) | Explicit anonymous context, internal denial, read-only service bearer token, restricted configuration fields, content suppression, fixed errors/diagnostics. |
| V. Human oversight | Scope bounded | No tools or handover in this increment; future capabilities must follow governance. |
| VI. Observability | PASS (design) | Native instrumentation to Langfuse, opaque bot/version/request/conversation/session correlation and reported usage/cost. Failure leakage tested. |
| VII–VIII. Maintainability and documentation | PASS (design) | Focused modules and typed boundary values; contracts and quickstart written. Implementation must add docstrings/README and pass checks. |
| IX. Testing and quality gates | PASS (design) | TestModel/FunctionModel, schema/AG-UI parity, error/cancellation/isolation tests. Producer/consumer conformance and bot regression gates precede activation. |
| X. Dependency release policy | **PASS — policy resolved** | Selected Pydantic AI and Langfuse releases are stable major versions. Required OTEL beta packages are permitted upstream dependencies; implementation must resolve compatible exact versions into the committed lockfile. |
| XI. User experience | PASS (design) | Native streamed reply and exactly one terminal success or sanitized failure; frontend conformance prerequisite documented. |
| Fixed technologies and component boundaries | PASS (design) | Existing runtime plus public shared artifacts; Pydantic AI v2, AG-UI, LiteLLM, and Langfuse preserved. |

**Pre-design outcome**: PASS under constitution 2.1.0. Stable selected core libraries and their required coordinated upstream dependencies are permitted with compatibility and committed exact resolution. No constitutional violation is proposed.

**Post-design outcome**: PASS for design. Native APIs and boundaries satisfy applicable principles with the verification obligations above. No unresolved technical clarifications remain. Installation, tests, producer/consumer deployment compatibility, and activation evaluations have not been executed or claimed by planning.

**Artifact validation**: Parsed all four contract JSON files, checked fixture identifiers/terminal-event consistency, verified local links across all eight Markdown files, and checked whitespace. A temporary isolated dependency/native-schema validation attempt failed because shell DNS could not resolve PyPI; no project manifest or lockfile was changed. Metadata/tagged-source research supports the selected APIs, but actual resolution and native schema/event validation remain mandatory implementation checks. The local syntax checker used the available Python 3.14 release candidate; application validation must use stable Python 3.14.

## Project Structure

### Documentation (this feature)

```text
specs/001-core-agent-backend/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── bot-spec-api.md
│   ├── bot-spec.schema.json
│   ├── agent-runtime.md
│   └── fixtures/
│       ├── bot-spec.json
│       ├── agent-request.json
│       └── agent-events.json
└── checklists/
    └── requirements.md
```

`tasks.md` belongs to `/speckit.tasks` and is not created by this command.

### Source Code (repository root)

```text
muchabo-backend/
├── main.py
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── README.md
├── muchabo/
│   ├── app.py
│   ├── settings.py
│   ├── bot_spec.py
│   ├── agent.py
│   └── telemetry.py
└── test/
    ├── test_app.py
    ├── test_bot_spec.py
    ├── test_agent.py
    └── test_telemetry.py

contracts/bot-spec/          # Shared public schema and fixtures, packaged by both backends.
```

**Structure Decision**: Retain the existing flat backend layout. `app.py` owns HTTP/lifecycle; `settings.py` owns required runtime settings; `bot_spec.py` owns the strict platform boundary and async fetch (FR-002/003); `agent.py` uses native execution/streaming and terminal sanitization (FR-001/004/005/006); `telemetry.py` owns instrumentation setup/teardown and fixed diagnostic allowlists (FR-008). No agent-service class, wrapper, registry, abstract base, or custom configuration format. Public docstrings and a short README explain each responsibility (FR-007/010).

Implementation must add the missing lockfile, publish shared contracts, and include them in component builds. Change the Python Docker build context to repository root with narrowly scoped COPY paths; update `compose.yaml` and Python image workflow contexts accordingly. Add public contract paths to affected CI filters and frozen Python install/formatter/type checks. Admin endpoint/UI code is outside this increment; its packaging/conformance obligations are documented for the integration owner.

## Complexity Tracking

### Implementation outcome

Implementation follows constitution 2.1.1: every Python operation uses uv and
installation is frozen. Native AgentSpec, explicit LiteLLM provider, adapter APIs,
timeout callback and native Langfuse masking/exporter hooks were verified against
the installed pinned packages. User-installed supporting updates were retained:
pydantic-settings 2.16.2, pytest 9.2.0 and ty 0.0.94. jsonschema 4.26.0 is dev-only.

All core acceptance and quality checks passed; current results are recorded in
quickstart. Podman built and ran the Linux image with stable Python 3.14.4, a
non-root user, bundled contracts and a controlled first reply. Actual build fixes
retain UBI 10.1 while pinning its published multi-platform digest, install the
missing user-management utility, and put the managed interpreter in a non-root-readable
location outside /root. main.py/port 8080 remain the runtime entry path through uv.

The shared identifier schema explicitly excludes non-identifier characters so
JSON Schema's trailing-newline anchor behavior matches native validation. Native
usage is emitted once at the model-call level; owned request diagnostics do not
duplicate model usage. Langfuse exports only the runtime/native instrumentation
scopes and the fixed attribute allowlist. Live producer/frontend/evaluation
prerequisites remain external and are not claimed by controlled consumer proof.

No prohibition is waived. Pydantic AI serves the requested agent execution, AG-UI, and native configuration capabilities; Langfuse serves mandatory tracing. Existing FastAPI and the standard library cannot provide these framework capabilities. Slim installation minimizes unused integrations.

| Dependency consideration | Why needed | Policy and verification |
|--------------------------|------------|-------------------------|
| Coordinated OTEL upstream dependencies | Required by stable Langfuse/OpenTelemetry packages for mandated tracing. | Permitted by constitution 2.1.0; preserve declared compatibility and lock the complete resolved graph. No tracing replacement or custom exporter is needed. |
| Typed terminal-event sanitization | Native adapter exposes raw errors and treats timeouts as cancellation success. | Small event filter plus native callback satisfies current failure/privacy requirements; keep native encoding and avoid subclassing/wrapping the agent framework. |
| Shared schema packaging / build context | Both backends must validate the same public contract; existing Python build context excludes repository-level resources. | Package only the public contract and backend; no private cross-component import or new shared Python library. |
| Explicit existing-graph SDK pins | Direct OpenAI/AG-UI/OTEL APIs enforce retries, terminal events, and lifecycle. | Pin direct imports; do not install alternate client, protocol, or tracing frameworks. |
