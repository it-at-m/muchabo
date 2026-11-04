<!--
Sync Impact Report (temporary review material; remove before committing)
Version change: 1.0.0 → 2.1.1 (includes dependency-policy amendment from 2.0.0)
Rationale: incompatible redefinition of the governance baseline, fixed framework decisions,
  and mandatory quality gates replacing discretionary compliance exceptions.
Dependency-policy amendment: compatible expansion of permitted upstream dependencies;
stable-major requirements apply to directly selected core libraries, while required upstream
dependencies may use 0.x or prerelease versions when compatible and locked.
Modified principles (prior guidance redistributed into the following principles/section):
- I. Clear Component Boundaries → Technology and Operational Constraints; II. Config over Code
- II. Explicit Integration Contracts → II. Config over Code; IX. Testing and Quality Gates
- III. Evidence-Based Verification → IX. Testing and Quality Gates
- IV. Reproducible Builds and Configuration → X. Production Readiness;
  IV. Security and Data Protection by Design
- X. Production Readiness: clarify core-library scope and permit required upstream dependencies.
- V. Maintainable and Documented Changes → I. Simplicity First;
  VII. Clean, Maintainable Code; VIII. Documentation
Added principles: III. Stateless, Scalable Runtime; V. Human Oversight;
  VI. Observability; XI. User Experience.
Added sections: none; existing technology, workflow, and governance sections expanded.
Removed sections: none; discretionary compliance-exception procedure removed.
Amendment follow-up: core-agent-backend plan and research synchronized; dependency-policy
blocker resolved. No technology replacement or application migration required.
Tooling clarification (2.1.0 → 2.1.1): all Python operations MUST use uv commands,
including interpreter management, dependency operations, scripts, tests, and quality checks.
Existing frozen uv commands remain valid; future commands and documentation must follow this rule.
Deferred items:
- TODO(RATIFICATION_DATE): Maintainers must confirm the original adoption date;
  no ratification date was recorded in the prior constitution.
-->
# MuChaBo Constitution

## Core Principles

### I. Simplicity First

- Simplicity MUST have the highest priority in implementation choices across all four parts,
  while satisfying every applicable requirement and principle. Every feature MUST use the
  least code that meets its specification; the smallest change that works is the right change.
- Implementations MUST use built-in features of the chosen frameworks and existing libraries
  before adding custom code. The MuChaBo backend MUST prefer Pydantic AI agent specs,
  capabilities, toolsets, deferred tools for approvals, the AG-UI adapter, MCP toolsets, and
  instrumentation. Frontends MUST prefer existing UI components and the AG-UI client library.
- Code MUST NOT introduce wrapper layers around Pydantic AI or other core libraries.
- Code MUST NOT introduce abstract base classes, interfaces, factories, or registries for a
  single implementation. An abstraction MUST have a second real use before introduction.
- Code MUST NOT introduce plugin systems, generic frameworks, custom state-management layers,
  or configuration options without an explicitly requested requirement.
- Code MUST NOT implement hypothetical future requirements (YAGNI) or add a dependency when
  the standard library or an existing dependency already covers the need.
- Contributors SHOULD prefer deleting redundant code over adding code, because reducing the
  maintained surface is preferable when both changes meet the same requirement.

**Rationale:** Every line is maintenance cost, and coding agents tend to overengineer.

### II. Config over Code

- Bot behavior MUST be defined only by the bot spec. The MuChaBo backend and frontend MUST
  contain no bot-specific code; adding or changing a bot MUST require no code change or
  redeployment.
- Bot specs MUST map as directly as possible onto Pydantic AI agent specs rather than create
  a parallel custom agent format. Platform fields MUST cover the bot's system prompt, model,
  tools, MCP servers, knowledge sources, start suggestions, guardrails, approval requirements,
  and handover rules as needed by its specification.
- The admin backend MUST validate bot specs against the same schema used by the MuChaBo
  backend. Specs MUST be versioned, and the runtime MUST load a spec through the admin
  backend API at request time and identify the version used for execution.
- Invalid specs MUST fail fast with a clear validation error before bot execution.

**Rationale:** One shared runtime can serve many bots without duplicated implementations.

### III. Stateless, Scalable Runtime

- The MuChaBo backend MUST keep no conversation state in process memory between requests.
  Conversation history and pending approvals MUST be persisted externally.
- Any runtime instance MUST be able to continue any conversation, including a pending approval,
  from persisted state and authorised per-request context.
- I/O MUST be asynchronous throughout the MuChaBo runtime; request execution MUST NOT depend
  on blocking network or persistence operations.

**Rationale:** External state and asynchronous I/O enable horizontal scaling and reliable resumption.

### IV. Security and Data Protection by Design

- Public citizen bots and internal employee bots MUST have distinct trust levels. Public users
  MUST be treated as untrusted, including anonymous or lightly authenticated users; internal
  users MUST be authenticated and subject to role-based content and tool access.
- Both backends MUST authenticate every request according to its access policy, including
  service-to-service calls. Public anonymous access MUST use an explicit anonymous access
  context and MUST NOT grant employee privileges. The admin frontend and backend MUST be
  restricted to authorised administrators.
- Per-request user identity, tenant, and roles MUST be passed through Pydantic AI dependencies
  into tools, retrieval, and MCP calls. Each access MUST enforce least privilege; internal
  content access MUST be governed by LDAP/IdP authorisation. A bot spec MUST NOT elevate the
  caller's permissions.
- User input, retrieved content, and tool output MUST be treated as untrusted and MUST NOT
  override authorisation or approval controls through prompt injection.
- Secrets MUST NOT appear in code, bot specs, or frontend bundles. Credentials MUST be supplied
  through runtime configuration and MUST NOT be committed or embedded in build artifacts.
- All parts MUST comply with GDPR through data minimisation and defined retention periods.
  Logs and Langfuse traces MUST contain no unmasked personal data; masking MUST occur before
  telemetry is emitted.

**Rationale:** Different trust levels require enforced access boundaries and protection of personal data.

### V. Human Oversight

- Sensitive tool calls MUST require human approval before execution, using Pydantic AI deferred
  tools and AG-UI interrupts that the MuChaBo frontend renders as approval requests.
- Approval requirements MUST be defined in the bot spec; approval decisions MUST be bound to
  the pending action and checked against the approving user's permissions before resumption.
- Bots MUST support handing a conversation to a human agent, such as Zammad, with full context
  within the authorised scope and data-protection rules. Specs MAY permit taking the
  conversation back after handover.
- Bots MUST never claim to be human. Citizens MUST be clearly told when they are talking to AI,
  and the frontend MUST identify a transition between AI and human assistance.

**Rationale:** Human control and transparent handover preserve accountability for sensitive actions.

### VI. Observability

- Every bot run MUST be traced end to end in Langfuse through Pydantic AI's built-in
  OpenTelemetry instrumentation, covering LLM calls, tool calls, sub-agent calls, token usage,
  and cost.
- Traces MUST carry bot id, bot spec version, conversation id, and session/user id. Identifiers
  MUST be pseudonymised or masked where necessary to meet the data-protection principle;
  anonymous users MUST remain identifiable only within their permitted session context.
- Both backends MUST write structured logs that support correlation and diagnosis without
  disclosing secrets or unmasked personal data.

**Rationale:** Correlated traces and logs make bot behavior, failures, and costs explainable.

### VII. Clean, Maintainable Code

- All parts MUST use typed code: Python MUST have full type hints, and TypeScript MUST use
  strict mode.
- Linter, formatter, and type-checker checks MUST pass in CI with no exceptions.
- Modules MUST have small, single responsibilities, and implementation MUST be explicit rather
  than rely on hidden behavior. Code MUST follow the affected component's established naming
  and structure.
- Dead code and commented-out code MUST NOT be retained. Unrelated refactoring MUST NOT be
  bundled with a feature unless its necessity is explained in the plan.

**Rationale:** Consistent, typed, focused code is easier for humans and agents to change correctly.

### VIII. Documentation

- Every public module, class, function, and component MUST have a short docstring or the
  language-appropriate documentation comment.
- Comments MUST explain why a choice was made and clarify non-obvious logic; they MUST NOT
  merely narrate what the code obviously does.
- The bot spec format and bot spec API MUST be documented with examples, including validation,
  versioning, and error behavior. AG-UI integration interfaces MUST also be documented.
- Significant architecture decisions MUST be recorded as short architecture decision records
  (ADRs). Changes to setup, configuration, public behavior, or operating procedures MUST update
  the relevant README or `docs/` guidance in the same change.

**Rationale:** Concise, current documentation makes contracts and design intent usable without guesswork.

### IX. Testing and Quality Gates

- Every part MUST have unit tests for core logic. MuChaBo backend unit tests MUST use Pydantic
  AI test models instead of real LLM calls.
- Contract tests MUST cover the bot spec API and format and the AG-UI event stream, and MUST
  run on both sides of each interface.
- Integration tests MUST cover persistence and MCP interactions, including conversation and
  pending-approval resumption where affected.
- Each bot MUST have an evaluation/regression suite that passes before a spec or model change
  goes live. Failed evaluations MUST block activation of the change.
- Tests MUST remain as simple as the code and assert observable behavior. Test frameworks and
  fixtures MUST NOT be added beyond what the tested behavior requires.
- Applicable tests and quality gates MUST pass before merge. Documentation-only changes MUST
  be checked for consistency, references, and formatting.

**Rationale:** Focused tests and bot evaluations protect contracts and behavior without needless machinery.

### X. Production Readiness

- Directly selected core libraries, including the agent framework and tracing SDK, MUST use
  stable major releases and MUST NOT use beta or `0.x` releases. This restriction does not
  apply to required upstream dependencies or the established supporting stack.
- Required upstream dependencies MAY use `0.x` or prerelease versions when required by the
  selected libraries' declared dependency constraints. They MUST remain compatible with those
  constraints and MUST be resolved to exact versions in committed lockfiles. This includes
  coordinated OpenTelemetry dependencies required by the stable Langfuse SDK.
- Direct runtime dependencies MUST have exact pinned versions and a documented upgrade path;
  the complete resolved dependency graph MUST be recorded in committed lockfiles.
- Dependency changes MUST update manifests and committed lockfiles together. Builds MUST use
  locked installation paths, including frozen Python dependencies and clean npm installations
  where configured.
- All Python operations MUST use `uv` commands in local development, coding-agent sessions,
  CI, and container builds. Manage interpreters with `uv python`, dependencies and environments
  with `uv` commands, and execute Python scripts, diagnostics, tests, linters, and type checkers
  through `uv run`. Direct interpreter paths, bare `python`/`python3`, `pip`, and standalone
  Python-tool invocations MUST NOT bypass uv. Project execution MUST use `uv run --frozen`
  after lockfile creation; dependency installation MUST use `uv sync --frozen`.
- External calls MUST have explicit timeouts and bounded retries. Retry policy MUST account
  for side effects so an approved action is not inadvertently executed twice.
- Users MUST receive a meaningful response on failure instead of a raw error. Responses MUST
  preserve data-protection rules, while structured logs and traces provide diagnostic detail.

**Rationale:** Stable, reproducible dependencies and controlled failures make the platform operable.

### XI. User Experience

- The MuChaBo frontend MUST use plain, understandable language for citizens and meet
  WCAG 2.1 AA and BITV 2.0 accessibility requirements.
- Both frontends MUST show clear loading, error, and approval states. These states MUST be
  accessible and distinguish pending work from actions requiring a user's decision.
- The MuChaBo frontend MUST render streamed messages, tool calls, start suggestions, and
  approval requests from AG-UI without bot-specific UI code.

**Rationale:** Clear, accessible interaction lets citizens and employees use bots with confidence.

## Technology and Operational Constraints

MuChaBo is the Munich Chatbot Framework & Platform, serving many LLM-powered chatbots and agents
for use cases such as retrieval-augmented generation over knowledge sources, guided forms, and
FAQs. It hosts public bots for citizens and internal bots for employees.

The platform MUST retain four parts with these responsibilities:

1. **Admin frontend** (`admin-frontend/`): administrators create, edit, version, and test bot
   specifications through this UI.
2. **Admin backend** (`admin-backend/`): owns and stores bot specifications, validates them,
   and exposes them to the MuChaBo backend through the bot spec API.
3. **MuChaBo backend** (`muchabo-backend/`): one shared core runtime loads a bot spec from
   the admin backend at request time and executes the bot accordingly.
4. **MuChaBo frontend** (`muchabo-frontend/`): citizen and employee chat UI communicates with
   the runtime via AG-UI and renders streaming and interactive events.

Parts MUST communicate only through documented interfaces. The bot spec API defines the admin
backend-to-runtime boundary; AG-UI defines the runtime-to-chat-frontend boundary. The admin
frontend MUST access specifications through the admin backend API. Parts MUST NOT read another
part's database or rely on its private internals. Any embedding surface such as `webcomponent/`
MUST respect the same frontend boundary rather than introduce another runtime or bot-specific code.
Interface changes MUST identify affected consumers and preserve compatibility or document a
coordinated migration path.

The following technology decisions are fixed:

- **Agent framework:** Pydantic AI, current stable major version v2. The MuChaBo backend MUST
  use Pydantic AI's agent execution rather than a custom agent loop.
- **Tracing:** Langfuse, fed by Pydantic AI's built-in OpenTelemetry instrumentation.
- **Frontend protocol:** AG-UI, through Pydantic AI's built-in backend adapter and an existing
  AG-UI client library on the frontend.
- **External tools:** MCP, through Pydantic AI's built-in MCP support.
- **Model access:** LiteLLM as the model gateway; runtime model calls MUST use that gateway.

The existing supporting stack is Python with FastAPI and uv for the runtime, Vue 3 with
TypeScript and Vite for frontend surfaces, and container execution where Docker configuration
exists. Exact versions MUST be recorded in manifests and lockfiles rather than duplicated here.
Replacing a fixed technology decision MUST require a constitutional amendment.

The project MUST retain its MIT licensing and follow `CODE_OF_CONDUCT.md`. Contributions that
introduce third-party code or dependencies MUST identify applicable licensing obligations.

## Development Workflow and Review

Contributors MUST follow `CONTRIBUTING.md`: describe enhancements in an issue tagged
`enhancement`, work on a feature branch, and submit a pull request. Every specification, plan,
and pull request MUST be checked against all applicable principles and architecture constraints.

Plans MUST identify affected parts, interfaces, security context, verification, and any spec or
model evaluation required for activation. Any added complexity, including a new abstraction,
new dependency, or custom code where a framework built-in exists, MUST be justified in the
plan's **Complexity Tracking** section or rejected. A justification MUST establish a present
requirement and explain why existing facilities do not meet it; it MUST NOT waive a prohibition
in this constitution.

Pull requests MUST state intended behavior, affected components, verification results, and
compatibility or migration impact. Reviewers MUST reject unsubstantiated complexity and failing
quality gates. Required checks MUST pass before merge; bot evaluation gates MUST pass before
spec or model activation. Governance conflicts MUST be resolved by correcting the change or
amending this constitution, not by granting ad hoc exceptions.

## Governance

This constitution MUST take precedence over all other project guidance. `CONTRIBUTING.md`,
component READMEs, `docs/`, specifications, and plans MUST operate within its rules. Simplicity
is the highest-priority design principle, not permission to bypass security, oversight,
accessibility, or quality requirements.

Amendments MUST be proposed through a pull request with a rationale, affected principles,
compatibility impact, and required migration or documentation follow-up. A project maintainer
MUST approve an amendment before adoption. Every amendment MUST update the constitution version
and last amended date, preserving the original ratification date once confirmed.

Versions MUST use semantic versioning: MAJOR for removed or redefined principles or other
backward-incompatible governance changes; MINOR for new principles, new sections, or materially
expanded compatible guidance; PATCH for clarifications and other non-semantic corrections.
Governance dates MUST use ISO format `YYYY-MM-DD` once known.

Compliance reviews MUST occur for every spec, plan, and pull request and again when their scope
changes. Maintainers MUST ensure that fixed technology decisions, Complexity Tracking
justifications, and required quality gates are respected. Amendments MUST identify dependent
guidance requiring follow-up. The temporary Sync Impact Report MUST be removed before the
amended constitution is committed.

**Version**: 2.1.1 | **Ratified**: TODO(RATIFICATION_DATE): confirm original adoption date | **Last Amended**: 2026-10-29
