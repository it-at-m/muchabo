---
description: "Executable tasks for the minimal shared agent-serving backend"
---

# Tasks: Minimal Core Agent Backend

**Input**: Design documents from `specs/001-core-agent-backend/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts](contracts/agent-runtime.md), [quickstart.md](quickstart.md), and constitution 2.1.1.
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

- [X] T001 Verify stable Python 3.14, exact agent/tracing/SDK pins, stable jsonschema dev pin, lockfile and frozen installation/imports. Verified Python 3.14.4, jsonschema 4.26.0 and native APIs. Preserve user-installed supporting updates: pydantic-settings 2.16.2, pytest 9.2.0 and ty 0.0.94. All Python operations follow constitution 2.1.1 through uv.
- [X] T002 [P] Publish the designed bot schema and bot/request/event fixtures into `contracts/bot-spec/`, with artifact ownership, contract/native version and local-only schema-reference policy. Native AgentSpec field names preserved; generated-schema parity remains T013.

**Checkpoint**: Stable interpreter, exact direct pins, committed-ready lockfile, and public contract fixtures are available. The previous shell PyPI DNS failure is an execution prerequisite to resolve, not permission to bypass dependency verification.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared settings, controlled verification support, telemetry setup, and application resource lifetime.

**Prerequisite**: T001–T002 complete. T004 and T005 can run together after T003.

- [X] T003 Implement secret-aware service settings and startup validation in `muchabo-backend/muchabo/settings.py` using the quickstart environment names, loopback-only HTTP, and redacted startup errors.
- [X] T004 [P] Add controlled environment, authenticated admin MockTransport, native TestModel and local Langfuse exporter fixtures in `muchabo-backend/test/conftest.py`; disable live model requests and defer application imports. FunctionModel scenarios follow in US1.
- [X] T005 [P] Initialize owned native Langfuse/OTEL instrumentation, disable all content capture and media settings, filter exported attributes, and provide fixed diagnostics plus off-loop teardown in `muchabo-backend/muchabo/telemetry.py`. Integrated sentinel verification remains T009/T018.
- [X] T006 Wire settings, owned admin/gateway clients and telemetry into `muchabo-backend/muchabo/app.py` lifespan; gateway retry/timeout policy and health/client teardown verified by the passing foundation test. Stream drain integration remains US1.

**Checkpoint**: Foundation ready. No new story endpoint is needed to verify resource setup and health behavior with controlled fixtures.

## Phase 3: User Story 1 — Receive an Agent Reply (Priority: P1) 🎯 MVP

**Goal**: Serve one configured anonymous public agent per validated request through native AG-UI, with isolation, configuration refresh, bounded failures, and content-free tracing.

**Independent Test**: With a controlled admin response and native test model, submit one message to `POST /api/bots/demo/run`, parse the stream with native AG-UI types, and assert the expected assistant reply and exactly one successful terminal event. Then verify all invalid-input, access, failure, refresh, and isolation acceptance cases without live services.

### Tests for User Story 1

Write focused observable tests before the corresponding implementation; first failures must indicate absent behavior, not missing fixture setup. T007–T009 use different files and the completed shared fixtures.

- [X] T007 [P] [US1] Add shared-schema/native/admin contract tests in `muchabo-backend/test/test_bot_spec.py`: strict boundaries, unsupported fields, identity equality, authenticated reads, failure mapping, no redirect/retry/cache, measured five-second deadline and 64-KiB limit.
- [X] T008 [P] [US1] Add HTTP/native AG-UI tests in `muchabo-backend/test/test_agent.py`: exact reply, terminal exclusivity, all HTTP mappings, caller restrictions, pre-execution rejection and fixed sanitized execution/timeout errors.
- [X] T009 [P] [US1] Add integrated content/credential sentinel and fixed diagnostic/span allowlist tests in `muchabo-backend/test/test_telemetry.py` using the local exporter and real native tracing path.

### Implementation for User Story 1

- [X] T010 [US1] Implement strict versioned platform envelope containing native AgentSpec in `muchabo-backend/muchabo/bot_spec.py`, preserving all data-model field names, bounds and identity/access rules.
- [X] T011 [US1] Validate the literal model/instructions/optional-name native subset before native parsing; reject unknown fields, templates and unsupported capability/policy overrides.
- [X] T012 [US1] Implement direct bounded authenticated per-request admin fetch, fixed public mappings, no fallback/cache/retries/redirects and strict identity/content validation.
- [X] T013 [US1] Generate bundled native and supported schemas, publish valid/invalid fixtures and verify native/design/published parity with explicit cross-field equality. Add explicit non-identifier-character exclusion for portable trailing-newline rejection.
- [X] T014 [US1] Pass fresh immutable anonymous `CallerContext` through native deps: public tenant, no identity, empty roles, server request UUID and validated conversation/session UUIDs.
- [X] T015 [US1] Use direct per-request Agent.from_spec with explicit OpenAIChatModel/LiteLLMProvider, owned gateway client, zero retries and fixed 20/25/30-second policy plus native content-free Instrumentation.
- [X] T016 [US1] Consume/encode through native AGUIAdapter public APIs, sanitize terminal errors, use supported timeout cancellation callback, drain/close iterators and retain contexts throughout lazy body delivery.
- [X] T017 [US1] Implement strict bounded `POST /api/bots/{bot_id}/run`, native input parsing, fixed public errors, request UUID response header and anonymous access checks before model execution.
- [X] T018 [US1] Integrate opaque bot/version/request/conversation/session correlation during lazy streaming with `as_baggage=False`; integrated sentinel checks pass for successful and failed native runs.
- [X] T019 [US1] Verify ten sequential successes, ten simultaneous isolated contexts/replies, in-flight v1/next-request v2 refresh and native disconnect cleanup in `muchabo-backend/test/test_agent.py`.
- [X] T020 [US1] Run frozen focused suite: 92 passed in 10.81 seconds, with measured SC-001/003/004/005 outcomes recorded in quickstart. No live integration claims.

**Checkpoint**: US1 delivers the runtime MVP with valid configuration, explicit anonymous access, native stream outcomes, isolation, and tracing. It is independently demonstrable with controlled prerequisites; live activation still requires producer/consumer conformance.

## Phase 4: User Story 2 — Start the Core Service (Priority: P2)

**Goal**: A maintainer can install, start, and understand the core from a clean checkout using documented settings and reproducible builds.

**Independent Test**: Follow the documented frozen setup and startup instructions on stable Python 3.14 with prerequisites available, receive one agent reply without source edits within 10 minutes, and verify missing/invalid configuration fails clearly without revealing secrets. Review the four documented responsibilities against current requirements.

**Dependency**: US1 is required to complete the first-reply acceptance check. T021–T024 are file-independent and may run together after T020; earlier documentation drafting is possible but does not complete US2.

### Tests for User Story 2

- [X] T021 [P] [US2] Add startup/health/settings/lifespan tests in `muchabo-backend/test/test_app.py`: every missing required setting, invalid/redacted URLs and credentials, zero-call health, draining resources and off-loop telemetry shutdown. Twenty checks pass; integrated disconnect checks also pass.

### Implementation for User Story 2

- [X] T022 [P] [US2] Document frozen setup/check/start, all settings, fixed deadlines/retries, curl/SSE behavior, responsibility locations, native extension/upgrade policy and live service prerequisites in `muchabo-backend/README.md`, including Podman commands.
- [X] T023 [P] [US2] Use scoped root-context backend/contract COPY, frozen installation and secret-excluding `.dockerignore`; retain main.py/port/non-root UID. Constitution 2.1.1 requires uv entrypoint. Actual build fixes: pin published UBI 10.1 multi-platform digest, install user-management utility and place the managed interpreter outside /root for non-root access.
- [X] T024 [P] [US2] Align main/tagged Python image workflows with root context and explicit backend Dockerfile. Local Podman packaging checks verify schemas included and credential/test/unrelated component files excluded; remote workflow execution is not claimed.
- [X] T025 [US2] Build and run the root-context image through the user's Podman engine, verify UID/interpreter/schema packaging, and prove startup plus exact first reply in a network-disabled container with controlled substitutes (0.082 seconds after frozen installation). Startup tests pass; documented responsibility/requirement review passes. Live producer/frontend/model/tracing prerequisites remain external.

**Checkpoint**: US2's documented startup path and container packaging are reproducible, settings failures are clear, and a maintainer can trace the small core responsibilities.

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Enforce the existing quality gates and document public-contract handoff without expanding runtime capabilities.

- [X] T026 [P] Update backend CI to frozen uv installation/execution, Ruff lint/format and ty gates; include shared contracts in runtime/admin change filters while preserving existing action/build conventions. Changed YAML parses successfully.
- [X] T027 [P] Publish explicit Java schema/fixture packaging, spec-reader JWT issuer/audience/token lifecycle, frontend native AG-UI conformance and bot evaluation/activation handoff in public README and spec-read contract. Record scaffold gaps as external prerequisites.
- [X] T028 Review all five flat core modules for type hints, public documentation, current-requirement traceability and simplicity. Remove duplicated usage attribution, keep direct native APIs and confirm no speculative tools/persistence/approvals/handover/framework/bot-specific code.
- [X] T029 Complete final frozen verification: 116 tests, 97% coverage, Ruff lint/format and ty passed; Podman root-context rebuild and network-disabled non-root reply/tracing/schema packaging smoke passed. Four YAML configs, six public JSON artifacts/local references, 25 Markdown links and whitespace verified. Final evidence and unavailable live/remote CI prerequisites recorded in quickstart.

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
- All 29 implementation tasks are completed and marked `[X]`; evidence and external integration prerequisites are recorded in quickstart.
