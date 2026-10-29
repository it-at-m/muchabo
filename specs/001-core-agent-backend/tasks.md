---
description: "Executable tasks for the minimal shared agent-serving backend"
---

# Tasks: Minimal Core Agent Backend

**Input**: Design documents from `specs/001-core-agent-backend/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts](contracts/agent-runtime.md), [quickstart.md](quickstart.md), and constitution 2.1.0.
**Tests**: Included because the specification requires observable validation, isolation, failure, and diagnostic checks, and constitution IX requires core and contract tests. Use native Pydantic AI test models, not live-model unit tests.
**Organization**: Setup and foundations precede two story increments. No application implementation is performed by this task-generation command.

## Format: `[ID] [P?] [Story] Description`

- `[P]` identifies independent files in a dependency-ready execution wave; finish named prerequisites before launching that wave.
- `[US1]` is Receive an Agent Reply (P1); `[US2]` is Start the Core Service (P2).
- All paths are repository-relative. Preserve existing component layout and user changes.
- Tasks remain unchecked until their code and required verification are complete. Do not commit, push, or alter git branches without an explicit request.

## Path Conventions

- Runtime source: `muchabo-backend/muchabo/`; tests: `muchabo-backend/test/`.
- Published shared contract: `contracts/bot-spec/`; design source: `specs/001-core-agent-backend/contracts/`.
- Public schema resources are shared interfaces, not another component's private internals.
- Use flat modules and direct native library calls. Every new responsibility must map to a current requirement; extensibility does not justify speculative interfaces, registries, wrappers, or capability scaffolding.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish a reproducible, verified dependency baseline and publish the existing design fixtures.

- [ ] T001 Verify stable Python 3.14 using `muchabo-backend/.python-version`; preserve the existing supporting dependencies and add `pydantic-ai-slim[openai,ag-ui,spec]==2.63.0`, `langfuse==5.0.4`, `pydantic==2.14.1`, `openai==3.31.0`, `ag-ui-protocol==1.0.0`, and `opentelemetry-sdk==1.45.1` in `muchabo-backend/pyproject.toml`; resolve an exact stable `jsonschema` pin in the dev group solely for shared-schema parity tests, produce `muchabo-backend/uv.lock`, and verify frozen installation/imports. Respect constitution 2.1.0 for required upstream versions; if the actual graph or pinned APIs cannot be verified, report that blocker rather than silently change framework versions or claim success.
- [ ] T002 [P] Publish the designed bot schema and bot/request/event fixtures from `specs/001-core-agent-backend/contracts/` into `contracts/bot-spec/bot-spec.schema.json` and `contracts/bot-spec/fixtures/`; create `contracts/bot-spec/README.md` with contract version, pinned native framework version, artifact ownership, and local-only schema-reference policy. Preserve the native AgentSpec field names; final generated-schema parity is completed by T013.

**Checkpoint**: Stable interpreter, exact direct pins, committed-ready lockfile, and public contract fixtures are available. The previous shell PyPI DNS failure is an execution prerequisite to resolve, not permission to bypass dependency verification.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared settings, controlled verification support, telemetry setup, and application resource lifetime.

**Prerequisite**: T001–T002 complete. T004 and T005 can run together after T003.

- [ ] T003 Extend `muchabo-backend/muchabo/settings.py` with required admin base URL/service access token and LiteLLM API base/key, plus validation for Langfuse destination/project credentials; use secret-aware typed settings, reject missing/invalid settings before agent execution without exposing values, allow localhost HTTP only for local validation, and retain application name/log level. Use exactly the environment names in `specs/001-core-agent-backend/quickstart.md`; fixed timeout/retry policy introduces no extra tuning settings.
- [ ] T004 [P] Create minimal fixtures in `muchabo-backend/test/conftest.py` for controlled settings, authenticated admin MockTransport responses, native TestModel/FunctionModel runs, and an in-memory OTEL collector; set `ALLOW_MODEL_REQUESTS=False` and prevent external telemetry/network calls. Reuse `contracts/bot-spec/fixtures/` and avoid a new fixture framework or shared production interfaces; defer application imports until test environment is configured.
- [ ] T005 [P] Implement native Langfuse/owned-OTEL initialization and fixed structured diagnostic fields in `muchabo-backend/muchabo/telemetry.py`; disable content, binary content, and model-request-parameter capture, decorator IO capture, and media uploads. Allow only static event/error codes, request/conversation/session UUIDs, bot ID/version, model alias, duration, and reported token/cost counts; never emit prompts, replies, config bodies, secrets, raw exceptions, or stack traces. Provide off-event-loop Langfuse flush/shutdown and explicit owned-provider shutdown; no agent wrapper or per-request flush.
- [ ] T006 Wire validated settings and telemetry into the existing lifespan in `muchabo-backend/muchabo/app.py`; open application-owned admin httpx and AsyncOpenAI clients, configure gateway `max_retries=0` and HTTP timeout 20 seconds, retain native model request timeout 25 seconds and run timeout 30 seconds for story integration, and close resources only after active streams drain. Preserve `/` and `/api/healthz`; health must make no model/configuration call. This task depends on T003–T005 and does not invent an agent service class.

**Checkpoint**: Foundation ready. No new story endpoint is needed to verify resource setup and health behavior with controlled fixtures.

## Phase 3: User Story 1 — Receive an Agent Reply (Priority: P1) 🎯 MVP

**Goal**: Serve one configured anonymous public agent per validated request through native AG-UI, with isolation, configuration refresh, bounded failures, and content-free tracing.

**Independent Test**: With a controlled admin response and native test model, submit one message to `POST /api/bots/demo/run`, parse the stream with native AG-UI types, and assert the expected assistant reply and exactly one successful terminal event. Then verify all invalid-input, access, failure, refresh, and isolation acceptance cases without live services.

### Tests for User Story 1

Write focused observable tests before the corresponding implementation; first failures must indicate absent behavior, not missing fixture setup. T007–T009 use different files and the completed shared fixtures.

- [ ] T007 [P] [US1] Add bot-envelope/native-schema and admin-read contract tests in `muchabo-backend/test/test_bot_spec.py`; cover valid fixtures, strict types, length/pattern boundaries, unknown keys, nulls, forbidden templates/capabilities, path/name mismatches, missing active configs, bearer service headers, no redirects/cache/retries, the 5-second total fetch deadline, and 64-KiB response limit. Schema parity must compare Pydantic/native acceptance with the published Draft 2020-12 schema and explicitly enforce cross-field equality.
- [ ] T008 [P] [US1] Add runtime HTTP/AG-UI contract tests in `muchabo-backend/test/test_agent.py`; cover one exact controlled reply, native camelCase event parsing, terminal-event exclusivity, all documented 403/404/406/413/415/422/502/503 mappings, zero model calls on rejected requests, no caller identity elevation, sanitized execution errors, and timeout errors without a later RUN_FINISHED. Use fixed public messages from `specs/001-core-agent-backend/contracts/agent-runtime.md`.
- [ ] T009 [P] [US1] Add tracing/logging tests in `muchabo-backend/test/test_telemetry.py` using the in-memory collector; assert bot/version/request/conversation/session correlation, reported usage fields, and fixed allowed diagnostics for successful and failed runs. Seed caller text, configuration instructions, exceptions, and credentials with distinctive test secrets/personal-data sentinels and verify absence from exported spans/events/logs; verify flush/provider teardown without real Langfuse calls.

### Implementation for User Story 1

- [ ] T010 [US1] Define the strict platform envelope containing native AgentSpec in `muchabo-backend/muchabo/bot_spec.py`: `schema_version` is a string with “Exactly `"1"`; reject numbers, booleans, and coercion. Contract version, distinct from bot version.”; `bot_id` has “1–64 characters; `^[a-z0-9][a-z0-9_-]*$`; must equal the requested path identifier.”; `version` has “1–64 characters; same identifier pattern; immutable label for this bot definition.”; `access_policy` is “`anonymous` or `authenticated`; the current runtime executes only `anonymous`.” Reject unknown envelope keys and maintain strict JSON types without a replacement agent format.
- [ ] T011 [US1] Implement supported native-AgentSpec boundary checks in `muchabo-backend/muchabo/bot_spec.py`: “Required `model` and `instructions`; optional `name`; other keys rejected in this increment.”; `agent.model` is “Non-whitespace, 1–128 characters; gateway alias, never a credential or caller-selected URL.”; `agent.instructions` is “Non-whitespace, 1–16,000 characters; literal instructions. Template syntax is rejected in this increment.”; `agent.name` is “Optional, same identifier restrictions as `bot_id`; if present, equal to `bot_id`. Runtime uses `bot_id` as its non-personal agent name.” Reject unsupported raw keys before native parsing; enforce the schema's `{{`/`}}` prohibition and do not permit capabilities, metadata, schemas, model settings, tools, or credentials to override runtime policy.
- [ ] T012 [US1] Implement the direct async admin fetch in `muchabo-backend/muchabo/bot_spec.py` using the shared client: `GET /api/v1/bots/{bot_id}/spec`, bearer service token plus server X-Request-ID, 5-second total deadline, zero retries/redirects/cache, configured origin only, and 64-KiB limit. Validate JSON/content contract and loaded bot ID/version; map producer 404 to BOT_UNAVAILABLE, other fetch/auth failures to CONFIGURATION_UNAVAILABLE, and malformed/mismatched/oversized responses to INVALID_CONFIGURATION without forwarding producer details.
- [ ] T013 [US1] Export the pinned native AgentSpec schema to `contracts/bot-spec/native-agent-spec.schema.json` and export matching supported-envelope constraints from `muchabo-backend/muchabo/bot_spec.py` to `contracts/bot-spec/bot-spec.schema.json`; update the shared valid/invalid fixture corpus in `contracts/bot-spec/fixtures/` and finalize parity tests in `muchabo-backend/test/test_bot_spec.py`. Preserve the design's accepted field names/types, use only bundled schema references, and keep path/name equality explicit rather than assume portable JSON Schema can express it.
- [ ] T014 [US1] Define fresh typed anonymous caller context in `muchabo-backend/muchabo/agent.py`: `access_policy` is “Server-set `anonymous`; no employee authentication inferred.”; `user_id` is “`None`; no personal identity captured.”; `tenant` is “Server-set `public` for this increment; no internal tenant access.”; `roles` is “Empty tuple; cannot be supplied or elevated by the caller or bot configuration.”; `request_id` is “Server-generated UUID; returned as `X-Request-ID`.”; `conversation_id` is “Validated AG-UI `threadId`; no persistence/resumption semantics.”; `session_id` is “Same opaque UUID as `conversation_id` for this single-interaction scope.” Deny authenticated configs before model execution, keep service identity separate, and pass context directly through native dependencies.
- [ ] T015 [US1] Create the per-request native Agent directly in `muchabo-backend/muchabo/agent.py` from the loaded native spec using an explicit OpenAIChatModel and LiteLLMProvider with the application-owned AsyncOpenAI client; enforce zero agent/SDK retries, 20-second HTTP attempt, 25-second native model request, and 30-second run deadline. Supply native Instrumentation with the existing content-free settings, override the execution name with validated bot ID, and prevent model prefixes or config fields from selecting another provider; no factory, registry, wrapper class, or custom execution loop.
- [ ] T016 [US1] Implement native adapter stream consumption and terminal sanitization in `muchabo-backend/muchabo/agent.py` using AGUIAdapter.from_request/run_stream/streaming_response, per-run deps/metadata/UUID run ID, and the supported on_cancel callback for RunTimedOut. Emit a fresh fixed RUN_FAILED or RUN_TIMEOUT error event, suppress subsequent events after a terminal error while draining/closing native iterators, and keep resource contexts open throughout body consumption. Preserve native protocol transformation/encoding and propagate disconnect cancellation; do not invent on_error keywords or subclass event streams.
- [ ] T017 [US1] Add `POST /api/bots/{bot_id}/run` and pre-stream validation/error responses in `muchabo-backend/muchabo/app.py`: path `bot_id` has “Same identifier rules as configuration.”; `threadId`/`runId` are “UUID strings; correlation inputs only, never evidence of identity or stored history.”; `messages` is “Exactly one user message with UUID `id` and a string `content` containing non-whitespace; maximum 16,000 characters.”; `state` is “Exactly `{}`.”; `tools`/`context` are “Exactly `[]`.”; `forwardedProps` is “Omitted or exactly `{}`.” Enforce 64-KiB body, JSON input/SSE accept types, reject unknown/message extras and unsupported content without normalizing it, return all contract HTTP codes and fixed code/message/request_id bodies, attach server X-Request-ID, and make zero model calls before successful validation/access checks.
- [ ] T018 [US1] Integrate bot ID/version and opaque request/conversation/session correlation across request execution in `muchabo-backend/muchabo/agent.py`, `muchabo-backend/muchabo/app.py`, and `muchabo-backend/muchabo/telemetry.py`; keep propagation active during lazy streaming, use `as_baggage=False`, retain the fixed diagnostic allowlist, and attribute failures to the loaded version without exposing content. Run the T009 sentinel checks against the integrated path, not only a mocked logging function.
- [ ] T019 [US1] Extend `muchabo-backend/test/test_agent.py` with ten successful controlled interactions, ten simultaneous requests with distinct contexts/messages, per-request configuration refresh from v1 to v2 while an in-flight v1 retains its attribution, and disconnect/stream cleanup. Assert exact controlled outputs, zero leakage, no retained conversation state, no runtime redeploy for refresh, and cancellation/resource cleanup using native test models and controlled admin responses.
- [ ] T020 [US1] Run the focused US1 checks in `muchabo-backend/test/test_bot_spec.py`, `muchabo-backend/test/test_agent.py`, and `muchabo-backend/test/test_telemetry.py` with frozen dependencies, fix observed failures in the corresponding runtime modules, and record measured SC-001/003/004/005 outcomes in `specs/001-core-agent-backend/quickstart.md`. Do not report live admin/frontend integration from mocked consumer tests.

**Checkpoint**: US1 delivers the runtime MVP with valid configuration, explicit anonymous access, native stream outcomes, isolation, and tracing. It is independently demonstrable with controlled prerequisites; live activation still requires producer/consumer conformance.

## Phase 4: User Story 2 — Start the Core Service (Priority: P2)

**Goal**: A maintainer can install, start, and understand the core from a clean checkout using documented settings and reproducible builds.

**Independent Test**: Follow the documented frozen setup and startup instructions on stable Python 3.14 with prerequisites available, receive one agent reply without source edits within 10 minutes, and verify missing/invalid configuration fails clearly without revealing secrets. Review the four documented responsibilities against current requirements.

**Dependency**: US1 is required to complete the first-reply acceptance check. T021–T024 are file-independent and may run together after T020; earlier documentation drafting is possible but does not complete US2.

### Tests for User Story 2

- [ ] T021 [P] [US2] Extend `muchabo-backend/test/test_app.py` with startup/settings/lifespan checks for valid configuration, each missing/invalid required setting, redacted credential/URL validation failures, health with zero agent/config fetches, and clients/telemetry closing after consumed or disconnected streams. Use shared controlled settings and stable-Python dependency installation; do not invoke live services or add an auth framework.

### Implementation for User Story 2

- [ ] T022 [P] [US2] Update `muchabo-backend/README.md` with frozen installation/start/check commands, every environment variable from `specs/001-core-agent-backend/quickstart.md`, fixed 5/20/25/30-second deadlines and zero retries, curl request/expected terminal outcomes, external service/read-token prerequisites, and short locations/purposes for configuration, caller context, execution, reply delivery, and tracing. Document extension through native capabilities only when concrete features require it, upgrade/lockfile/schema procedures, and failure behavior; include no real secrets or production hardcoded bot.
- [ ] T023 [P] [US2] Update `muchabo-backend/Dockerfile` and `compose.yaml` for repository-root backend build context, scoped COPY of `muchabo-backend/` plus `contracts/bot-spec/`, locked installation, unchanged runtime entrypoint/non-root user, and bundled trusted schemas. Add a root `.dockerignore` for this backend context that excludes secrets and unrelated build content while preserving the backend and public contract inputs; inspect the existing `muchabo-backend/.dockerignore` before reusing its rules.
- [ ] T024 [P] [US2] Update the Python image-build sections of `.github/workflows/build.yml` and `.github/workflows/docker-release-backend.yml` to use repository-root context with explicit `muchabo-backend/Dockerfile`, matching T023's designed layout; leave other component build contexts consistent with their existing builds. Verify that tagged and main-branch backend builds package public schemas and contain no credential files.
- [ ] T025 [US2] Validate the install/start/curl and container scenarios in `specs/001-core-agent-backend/quickstart.md` against `muchabo-backend/README.md` and `muchabo-backend/Dockerfile`; run T021 startup checks, build the image with root context, and record first-reply setup time for SC-002 plus maintainer responsibility review for SC-006. Use controlled service substitutes for automated proof; record which live prerequisite checks are actually available rather than marking unavailable live deployment checks successful.

**Checkpoint**: US2's documented startup path and container packaging are reproducible, settings failures are clear, and a maintainer can trace the small core responsibilities.

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Enforce the existing quality gates and document public-contract handoff without expanding runtime capabilities.

- [ ] T026 [P] Update `.github/workflows/backend-tests.yml` and the Python/check-change sections of `.github/workflows/build.yml` to use `uv sync --frozen --group dev` and frozen test execution, enforce Ruff lint/format and ty checks for Python, and include `contracts/bot-spec/**` in affected runtime/admin component change filters. Preserve existing framework/action conventions; contract-only changes must trigger relevant validation/builds.
- [ ] T027 [P] Finalize public producer/consumer handoff in `contracts/bot-spec/README.md` and `specs/001-core-agent-backend/contracts/bot-spec-api.md`: list shared schema/fixture packaging requirements for the Java producer, dedicated JWT spec-reader identity/audience/issuer prerequisites, frontend AG-UI fixture conformance, and passing bot evaluation/regression evidence before live activation. Record existing component gaps as integration prerequisites; do not implement configuration CRUD, token issuance, frontend UI, or a new bot-evaluation framework in this runtime feature.
- [ ] T028 Review `muchabo-backend/muchabo/app.py`, `muchabo-backend/muchabo/settings.py`, `muchabo-backend/muchabo/bot_spec.py`, `muchabo-backend/muchabo/agent.py`, and `muchabo-backend/muchabo/telemetry.py` for full type hints, short public docstrings, current-requirement traceability, and consistency with existing layout; remove only feature-introduced dead code or unnecessary abstractions. Confirm FR-009/010 and SC-006: no tools, persistence, approval/handover scaffolding, single-implementation interfaces, or bot-specific runtime behavior.
- [ ] T029 Execute the full commands in `specs/001-core-agent-backend/quickstart.md` and backend container build with frozen dependencies, verify published schema/native-agent/AG-UI parity and all core tests, and record final results plus any unavailable live producer/frontend/evaluation prerequisites in `specs/001-core-agent-backend/quickstart.md`. Verify JSON/Markdown links and whitespace, inspect `muchabo-backend/pyproject.toml` with `muchabo-backend/uv.lock` for reproducibility, and fix only failures relevant to this feature before marking completion.

## Dependencies & Execution Order

### Phase Dependencies

```text
Setup:       T001 ─┐
                  ├→ T003 → (T004 ∥ T005) → T006
             T002 ┘
US1:         (T007 ∥ T008 ∥ T009)
                  → T010 → T011 → T012 → T013
                  → T014 → T015 → T016 → T017 → T018 → T019 → T020
US2:         (T021 ∥ T022 ∥ T023 ∥ T024) → T025
Polish:      (T026 ∥ T027) → T028 → T029
```

- Setup T001/T002 may proceed concurrently; all story work waits for foundation T003–T006.
- US1 needs no completed US2 work. T007–T009 test independent files against the established fixtures.
- Within US1, same-file model/fetch tasks T010–T012 are sequential. T013 requires their validators. T015 requires caller/config values; endpoint T017 requires native execution/streaming. Integrated correlation and isolation checks follow the endpoint.
- US2 completes after US1 because first agent reply is part of its acceptance criteria; its documentation, startup tests, Dockerfile/compose, and image workflow edits can share a parallel wave.
- T024 and T026 both edit `.github/workflows/build.yml` and must not run together. T021 and earlier US1 test edits also must respect their checkpoints. Do not assume every task in a phase is independent.
- Final T029 waits for all selected story and cross-cutting tasks.

### Parallel Opportunities

- Setup: T001 dependency resolution and T002 publishing current design resources.
- Foundations: T004 controlled test fixtures and T005 telemetry after settings T003.
- US1: T007 bot-spec tests, T008 runtime contract tests, and T009 telemetry tests.
- US2: T021 startup tests, T022 README, T023 Docker/compose layout, and T024 image-build workflow context changes.
- Polish: T026 CI quality/filter updates and T027 integration handoff documentation.

## Parallel Example: User Story 1

After T006, work on these independent targets together:

```text
T007: Bot-spec/admin/schema checks in muchabo-backend/test/test_bot_spec.py
T008: HTTP/AG-UI outcome checks in muchabo-backend/test/test_agent.py
T009: Content-free telemetry checks in muchabo-backend/test/test_telemetry.py
```

Use the completed `conftest.py` fixtures; coordinate any discovered shared-fixture changes before resuming the independent files.

## Parallel Example: User Story 2

After T020, these targets have no file overlap:

```text
T021: Startup/lifespan tests in muchabo-backend/test/test_app.py
T022: Maintainer guide in muchabo-backend/README.md
T023: Runtime image layout in muchabo-backend/Dockerfile, compose.yaml, and .dockerignore
T024: Image build contexts in .github/workflows/build.yml and .github/workflows/docker-release-backend.yml
```

They use the already specified root-context design. Perform integrated startup/build verification only after all four finish.

## Requirement Coverage

| Requirement / outcome | Tasks |
|-----------------------|-------|
| FR-001 agent serving / SC-001 successful replies | T008, T014–T020 |
| FR-002 validation | T007, T010–T013, T017, T021 |
| FR-003 current versioned configuration / SC-005 refresh | T002, T007, T010–T013, T019–T020 |
| FR-004 request isolation / SC-004 concurrency | T004, T014–T019 |
| FR-005 permitted caller context | T008, T014, T017 |
| FR-006 bounded meaningful failures / SC-003 negative cases | T003, T006–T009, T012, T015–T021 |
| FR-007 reproducible setup / SC-002 first reply | T001, T003, T021–T026, T029 |
| FR-008 safe correlated diagnostics | T005, T009, T018–T020 |
| FR-009/010 minimal extensible scope / SC-006 maintainability | T022, T025, T027–T029 |
| Shared native schema / AG-UI conformance | T002, T007–T008, T013, T026–T027, T029 |

## Implementation Strategy

### MVP First (User Story 1)

1. Finish setup and foundation, verifying the actual stable interpreter, locked graph, and native APIs that planning could not execute.
2. Implement US1 directly through Pydantic AI/AG-UI with controlled admin/model/telemetry services.
3. Stop at T020 and demonstrate one reply plus the failure, refresh, isolation, and privacy checks. This is the runtime MVP, not proof of an implemented admin/frontend integration.
4. Complete US2 for the clean-checkout installation/documentation and packaged build acceptance.

### Incremental Delivery

1. Foundation provides settings, clients, native tracing, and deterministic verification.
2. US1 adds the sole current runtime capability: serving one agent per request.
3. US2 makes that capability reproducibly installable and understandable.
4. Final checks enforce shared-contract/quality obligations and document prerequisites for actual integration and bot activation.
5. Later features extend native capabilities through coordinated contract changes; they are not implemented ahead of their requirements.

## Notes

- No new bot configuration owner, persistence service, identity provider, frontend feature, or generic framework is part of these tasks.
- Service credentials and operational configuration stay external. Tests may use test-only substitutes; never ship a fallback hardcoded bot or grant employee privileges to anonymous callers.
- Actual schema/provider/adapter APIs must be verified after locked installation. If research metadata differs from the installed release, correct the affected design/task assumptions explicitly before implementation proceeds.
- Producer-side validation, frontend-side conformance, and bot evaluation/activation are required for live use. Consumer mocks alone do not satisfy those external gates; the task list documents the handoff rather than inventing unavailable passing evidence.
- All 29 tasks use the required unchecked checkbox, sequential ID, appropriate story/parallel labels, and repository-relative file paths.
