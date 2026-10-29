# Research: Minimal Core Agent Backend

**Date**: 2026-10-28
**Feature**: [spec.md](spec.md)
**Outcome**: Research and Phase 1 design complete on 2026-10-29 under constitution 2.1.0. No unresolved technical clarifications.

## 1. Agent framework and minimal installation

**Decision**: Use `pydantic-ai-slim[openai,ag-ui,spec]==2.63.0`, the minimal distribution of Pydantic AI for present requirements. Preserve Python 3.14 and the existing FastAPI application. Pin directly imported Pydantic `2.14.1`, OpenAI `3.31.0`, AG-UI protocol `1.0.0`, and OTEL SDK `1.45.1`; all are compatible declared candidates subject to final locked installation verification.

**Rationale**: Pydantic AI 2.63.0 is a published non-yanked stable v2 release. Metadata explicitly supports Python 3.14. Slim avoids unused model providers and optional integrations. Exact transitive versions require compatible lockfile resolution during implementation.

**Alternatives considered**: Full `pydantic-ai` adds unused integrations. A custom agent loop violates the fixed framework decision and simplicity principle. A 0.x agent-framework release is unnecessary and prohibited.

**Sources**:

- [Pydantic AI 2.63.0 on PyPI](https://pypi.org/project/pydantic-ai/2.63.0/)
- [Slim distribution 2.63.0 on PyPI](https://pypi.org/project/pydantic-ai-slim/2.63.0/)
- [Release-tag dependency metadata](https://github.com/pydantic/pydantic-ai/blob/v2.63.0/pydantic_ai_slim/pyproject.toml)

## 2. Configuration-driven execution

**Decision**: Use released `AgentSpec` and `Agent.from_spec(...)`; obtain the current versioned definition through the admin backend's documented HTTP interface per request. Keep platform identity/version alongside the native agent spec rather than invent a second agent definition language.

**Rationale**: Released fields include `model`, `name`, `instructions`, `model_settings`, `metadata`, `retries`, `end_strategy`, and `capabilities`. Future features can use native capabilities when needed. This increment needs only a text agent. The admin interface needs Phase 1 contract design and producer agreement; no existing bot-spec endpoint is assumed.

**Alternatives considered**: Hardcoded behavior, production runtime-local specs, a custom DSL, and a generic registry conflict with current requirements or governance.

**Limitations**: The capability-aware generated schema is stricter than ordinary AgentSpec parsing. `deps_schema` does not validate runtime dependency objects. JSON `output_schema` does not validate generated dictionary contents. Current docs mention `instrument`, but tagged AgentSpec 2.63.0 does not define that field; use the released instrumentation API. Validate platform fields explicitly and use the native schema for agent fields.

**Sources**:

- [Agent spec guide](https://pydantic.dev/docs/ai/core-concepts/agent-spec/)
- [Release-tag AgentSpec](https://github.com/pydantic/pydantic-ai/blob/v2.63.0/pydantic_ai_slim/pydantic_ai/agent/spec.py)

## 3. Frontend boundary

**Decision**: Use `pydantic_ai.ui.ag_ui.AGUIAdapter.dispatch_request(...)` from an async FastAPI endpoint, returning its streaming Starlette response. Final route, validation rules, and errors belong in Phase 1.

**Rationale**: Native AG-UI supplies message/event schemas and SSE encoding without a custom protocol. The adapter accepts per-request dependencies and a whole-run timeout.

**Alternatives considered**: Custom JSON chat replaces the required frontend contract. Custom SSE encoding duplicates a library facility. Persistent shared state is outside this increment.

**Limitations**: Unsupported state/history must be explicitly bounded by the single-message contract. Native timeout/cancellation uses protocol completion and callbacks; verify meaningful caller failure where required. Client disconnect cancellation does not invoke the normal cancellation callback.

**Source**: [AG-UI integration](https://pydantic.dev/docs/ai/integrations/ui/ag-ui/).

## 4. Model gateway and resource bounds

**Decision**: Use `OpenAIChatModel` with released `LiteLLMProvider(api_base=..., api_key=...)`, connecting to the external gateway. Use native async model/agent operations and timeout settings.

**Rationale**: The provider uses an asynchronous OpenAI HTTP client; the runtime needs neither the LiteLLM Python package nor another gateway. Existing httpx remains suitable for admin configuration access.

**Alternatives considered**: Direct upstream calls bypass the gateway. Blocking calls violate asynchronous runtime requirements. Infinite retries violate production-readiness rules.

**Limitations**: Chat Completions is not universal Responses API compatibility. Capabilities depend on the gateway/model; aliases may need explicit profiles. Distinguish per-attempt `timeout`, model-request `request_timeout`, and whole-run `timeout`; final durations and finite retry limits belong in design. Whole-run timeouts use asyncio. Client ownership must last through stream consumption and close afterward.

**Sources**:

- [LiteLLM integration](https://pydantic.dev/docs/ai/models/compatible-apis/#litellm)
- [Release-tag timeout documentation](https://github.com/pydantic/pydantic-ai/blob/v2.63.0/docs/timeouts.md)
- [Model client lifecycle](https://pydantic.dev/docs/ai/models/overview/)

## 5. Minimal tracing and privacy

**Decision**: Use `langfuse==5.0.4`, initializing its OpenTelemetry pipeline before agent instrumentation. Use `InstrumentationSettings(include_content=False, include_binary_content=False, include_model_request_parameters=False)` and opaque correlation through `propagate_attributes(...)` with `as_baggage=False`.

**Rationale**: Native instrumentation retains model identity and reported usage without prompts, completions, or tool payloads. Langfuse can infer cost from matching model prices. No tracing wrapper or duplicate generation spans are needed.

**Alternatives considered**: Raw-message logging violates data protection. Disabling tracing violates observability. A provider tracing wrapper duplicates native agent instrumentation.

**Limitations**: Content suppression is not a universal personal-data scrubber: names, descriptions, schemas, metadata, and other instrumentation need a non-personal allowlist. Legacy masking does not cover all third-party spans. Missing usage cannot be reconstructed from removed message text. `flush()` and `shutdown()` are synchronous; run them off the event loop at teardown. An application-owned OTEL provider needs explicit shutdown after draining streams and Langfuse workers.

**Sources**:

- [Langfuse Pydantic AI integration](https://langfuse.com/integrations/frameworks/pydantic-ai)
- [Masking](https://langfuse.com/docs/observability/features/masking)
- [Token and cost tracking](https://langfuse.com/docs/observability/features/token-and-cost-tracking)
- [Client lifecycle](https://langfuse.com/docs/observability/sdk/instrumentation#client-lifecycle--flushing)

## 6. Dependency policy and resolution

**Decision**: Retain stable Pydantic AI and Langfuse core libraries and allow their required compatible upstream dependencies, resolved to exact versions in committed lockfiles, under constitution 2.1.0.

**Rationale**: The original constitution 2.0.0 applied stable-only requirements to every runtime dependency, which conflicted with required tracing packages. The user-authorized amendment narrows the stable-major restriction to directly selected core libraries, explicitly permits required upstream 0.x/prerelease dependencies, and preserves compatibility, exact pins, and committed lockfiles. Verified package metadata yields:

| Dependency | Mandatory dependency evidence |
|------------|-------------------------------|
| `langfuse==5.0.4` | Requires SDK and OTLP HTTP exporter `>=1.45.0,<2`. |
| `opentelemetry-sdk==1.45.1` | Requires `opentelemetry-semantic-conventions==0.66b1`. |
| `opentelemetry-exporter-otlp-proto-http==1.45.1` | Requires beta OTLP common and HTTP transport packages from coordinated release `0.66b1`. |

These beta packages are required upstream dependencies, not directly selected core libraries. Constitution 2.1.0 permits them when they meet the selected libraries' declared constraints and are locked. The established supporting stack is also outside the core-library stable-major restriction.

**Alternatives considered**: Slim installation cannot remove tracing's mandatory dependencies. Older SDKs cannot be presumed compliant without verified metadata. Forcing unrelated stable versions violates declared constraints. Replacing tracing or creating a custom exporter conflicts with fixed technologies and simplicity.

**Resolution**: Dependency-policy gate passes under the amended rule; Phase 1 artifacts are complete. Resolve and verify the actual dependency graph during implementation. The amendment changes no fixed technology decision and requires no application migration.

**Primary evidence**:

- [Langfuse 5.0.4 exact metadata](https://pypi.org/pypi/langfuse/5.0.4/json)
- [OTEL SDK 1.45.1 exact metadata](https://pypi.org/pypi/opentelemetry-sdk/1.45.1/json)
- [OTLP HTTP exporter 1.45.1 exact metadata](https://pypi.org/pypi/opentelemetry-exporter-otlp-proto-http/1.45.1/json)

## 7. Verification and repository findings

**Decision**: Retain pytest and the current layout. Use TestModel/FunctionModel, `Agent.override(model=...)`, and `ALLOW_MODEL_REQUESTS=False` for deterministic checks. Cover success, validation, access denial, external failure, timeout, concurrent isolation, configuration refresh, and content-free correlated telemetry.

**Rationale**: Observable outcome checks avoid live-model costs and custom test infrastructure. Producer/consumer contract checks and bot evaluations remain required before activation.

**Alternatives considered**: Live-model unit tests are nondeterministic and costly. Implementation-mirroring tests do not prove interaction behavior. Testing absent persistence/MCP capabilities adds no value here.

**Repository findings**: The backend serves only root and health routes; settings contain application name and log level. Its Dockerfile expects a missing `uv.lock`. The admin backend is a separate Java component with a scaffold API, not an established bot-spec contract. Shared schema and producer compatibility require explicit design and verification. No source files or application manifests were changed by planning.

**Source**: [Pydantic AI testing](https://pydantic.dev/docs/ai/guides/testing/).

## 8. Public access and absent integration contracts

**Decision**: Define one anonymous-only runtime endpoint and the admin spec-read contract. Server creates empty-role anonymous context; `authenticated` configurations are denied before execution. Reuse the admin JWT resource-server boundary for a dedicated read-only service principal. Do not introduce employee auth, token issuance, or UI work.

**Rationale**: Repository inspection found no working bot-spec API or AG-UI frontend. The admin has JWT authentication/method security; its example reader/writer roles are not a production bot access policy. Runtime configuration, model gateway, and tracing are external prerequisites. Mocked services prove core behavior while producer/consumer tests remain required for live activation.

**Alternatives considered**: Trusting incoming identity headers or caller configuration grants unearned privileges. Building admin CRUD, an identity framework, or a frontend expands this minimal feature. Assume none of the scaffold routes serve bot specs.

**Evidence**: `admin-backend/src/main/java/de/muenchen/oss/refarch/backend/configuration/security/SecurityConfiguration.java`, `admin-backend/src/main/java/de/muenchen/oss/refarch/backend/security/Authorities.java`, `admin-backend/src/main/resources/application-local.yml`, `admin-backend/api-spec/refarch-backend.yaml`, `muchabo-frontend/src/App.vue`, and `muchabo-frontend/package.json`.

## 9. Typed terminal events and streaming lifetime

**Decision**: Use AGUIAdapter.from_request/run_stream/streaming_response, its public on_cancel event callback, and a minimal request-local typed event filter. Create fresh sanitized RunErrorEvent values; drain/close the native iterator and suppress later terminal success. Resources and tracing context span body consumption.

**Rationale**: Pinned native on_error emits `str(error)`; native timeout normally emits RUN_FINISHED. There is no public `on_error=` callback parameter. A small terminal filter is required by the feature's meaningful-error/privacy rules without a custom encoder or agent wrapper. from_spec accepts an explicit Model override and native instrumentation capability, so model-name prefixes cannot select providers.

**Alternatives considered**: Bare dispatch_request leaks raw errors and has unsuitable timeout semantics. Library event-stream subclassing adds maintenance. Returning a response from an endpoint-local agent context closes resources too early.

**Sources**:

- [Pinned adapter APIs](https://github.com/pydantic/pydantic-ai/blob/v2.63.0/pydantic_ai_slim/pydantic_ai/ui/_adapter.py)
- [Pinned AG-UI lifecycle/error hooks](https://github.com/pydantic/pydantic-ai/blob/v2.63.0/pydantic_ai_slim/pydantic_ai/ui/ag_ui/_event_stream.py)
- [Pinned Agent.from_spec](https://github.com/pydantic/pydantic-ai/blob/v2.63.0/pydantic_ai_slim/pydantic_ai/agent/__init__.py)
- [AG-UI lifecycle](https://docs.ag-ui.com/spec/1.0/events/lifecycle)

## 10. Shared schema, native subset, and bounds

**Decision**: Platform envelope contains native AgentSpec; support only literal model/instructions and optional opaque name now. Use shared Draft 2020-12 schema and fixture parity across Python and Java; native parsing plus small strict boundary checks enforce runtime behavior. Preserve compatible field names for future native extensions. Publish public contract resources during implementation and package them explicitly.

**Rationale**: Pydantic validators do not automatically express every rule in exported JSON Schema. Use json_schema_extra/schema facilities for matching constraints and cross-field checks on both sides. Required schema sharing justifies packaging/CI changes, not a new shared Python framework. Fixed 5/20/25/30-second deadlines and zero config/SDK/agent retries satisfy bounded execution without new tuning options.

**Alternatives considered**: A duplicate custom agent format drifts from the library. Unrestricted capabilities/templates enable features outside scope. Accepting caller-supplied schema URLs or model clients crosses trust boundaries. A new Python production schema-validator abstraction is unnecessary.

**Sources**:

- [Pydantic validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [Pydantic JSON Schema customization](https://docs.pydantic.dev/latest/concepts/json_schema/)
- [OpenAI 3.31.0 metadata and retry/timeout configuration](https://pypi.org/pypi/openai/3.31.0/json)
- [AG-UI 1.0.0 release metadata](https://pypi.org/project/ag-ui-protocol/1.0.0/)

## Planning verification record

Local checks parsed all four JSON artifacts and verified fixture UUIDs, one success terminal event, every relative Markdown link, and whitespace. Isolated installation/native-model validation could not run because the shell's PyPI DNS lookup failed. No application dependencies or lockfiles were installed/changed. Final dependency resolution and native AgentSpec/AG-UI/schema parity are implementation gates, not completed planning tests. Documentation/API research is distinct from executing the candidate stack.
