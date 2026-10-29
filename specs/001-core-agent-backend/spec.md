# Feature Specification: Minimal Core Agent Backend

**Feature Branch**: `chore/init-speckit-constitution`

**Created**: 2026-10-28

**Status**: Draft

**Input**: User description: "setup the core of the whole core agent backend with pydantic. only the minimal core that does nothing but serving an agent. add pydanticai dep"

## Clarifications

### Session 2026-10-28

- Q: What role must this core serve in the wider project? → A: It establishes the foundation for the whole project and must remain simple and extensible. Future capabilities build on the same runtime using existing library capabilities as needed; this increment remains limited to agent serving.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Receive an Agent Reply (Priority: P1)

As a caller of the chatbot service, I want to send a message to a configured agent and receive its reply so that I can use the core runtime before additional chatbot capabilities are introduced.

**Why this priority**: Serving an agent is the entire purpose of this feature and the smallest useful foundation for the platform.

**Independent Test**: Start the service with a valid agent configuration and a controlled response source, submit one message through the supported chat interaction, and verify that the caller receives the expected reply and a completion indication.

**Acceptance Scenarios**:

1. **Given** a running service, a valid agent configuration, and an allowed caller, **When** the caller submits a non-empty message, **Then** the configured agent processes that message and the caller receives its reply and a completion indication.
2. **Given** two independent requests with different caller messages, **When** the service processes them, **Then** neither request receives content or conversation context belonging to the other request.
3. **Given** a supported configuration change available from the configuration owner, **When** a subsequent request is made, **Then** the service uses the current configuration without a runtime code change or redeployment.

---

### User Story 2 - Start the Core Service (Priority: P2)

As a maintainer, I want to install and start the core service using documented steps so that I can verify agent serving from a clean checkout.

**Why this priority**: A reproducible startup path makes the minimal runtime usable by contributors and operators.

**Independent Test**: Follow the backend setup instructions from a clean checkout with the required external services available, start the service, and complete one agent interaction.

**Acceptance Scenarios**:

1. **Given** a clean checkout and the documented prerequisites, **When** the maintainer follows the installation and startup instructions, **Then** the service starts and can serve an agent request without source edits.
2. **Given** missing or invalid required runtime configuration, **When** the maintainer starts the service or makes the first affected request, **Then** the service identifies the missing or invalid setting before agent execution and does not disclose credentials.
3. **Given** the delivered core and its maintainer documentation, **When** a maintainer reviews how configuration, caller context, agent execution, and reply delivery fit together, **Then** each responsibility has a documented location and purpose tied to this feature, and the documentation identifies how later agent capabilities can build on the same runtime.

### Edge Cases

- An empty, whitespace-only, or malformed message is rejected with an understandable validation outcome before agent execution.
- An unavailable or invalid agent configuration produces an understandable failure without running an agent with guessed settings.
- A model-service failure or timeout terminates the interaction with an understandable failure rather than leaving the caller waiting indefinitely.
- A request outside the permitted access policy is rejected before agent execution; permitted anonymous requests have no employee privileges.
- Concurrent independent requests cannot share caller identity, messages, or agent execution context.
- Failures and diagnostic records do not disclose credentials or unmasked personal data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The service MUST accept a non-empty caller message and serve one configured agent through the platform's existing chat interaction contract, delivering the agent reply and an unambiguous completion or failure outcome. This is demonstrated by User Story 1, scenario 1.
- **FR-002**: The service MUST validate the caller message and agent configuration before execution and reject invalid inputs with an understandable reason. This is demonstrated by the invalid-input edge cases and User Story 2, scenario 2.
- **FR-003**: The service MUST obtain the current agent configuration from its designated configuration owner for each request, including its identity, version, instructions, and selected model. Agent behavior MUST require no bot-specific runtime code. This is demonstrated by User Story 1, scenario 3.
- **FR-004**: The service MUST keep independent requests isolated and retain no conversation state in process memory between requests. This is demonstrated by User Story 1, scenario 2, including concurrent requests.
- **FR-005**: The service MUST apply the established access policy before agent execution, including an explicit anonymous context when anonymous access is permitted. Requests outside that policy MUST be rejected without invoking the agent.
- **FR-006**: The service MUST return a meaningful failure when a required external service fails, with an explicit execution timeout and finite retry limit documented for operators. Verification MUST include an unavailable configuration source and a nonresponding model source.
- **FR-007**: Maintainers MUST have a documented, reproducible installation and startup path with all required settings and prerequisites identified. This is demonstrated by User Story 2, scenario 1.
- **FR-008**: Each agent interaction MUST have correlated execution diagnostics identifying the agent and configuration version, with caller and interaction identifiers protected as required by the project's data-protection rules. Verification MUST confirm correlation for both success and failure and the absence of credentials or unmasked personal data.
- **FR-009**: This first increment MUST be limited to starting the runtime and serving a single agent per request. Agent tools, knowledge retrieval, multi-agent coordination, approval workflows, human handover, configuration management screens, and persistent conversation management are deferred to later features; their exclusion here is not a permanent restriction on the shared runtime.
- **FR-010**: The core MUST provide a foundation that later features can extend within the existing component responsibilities and documented interaction contracts. Each responsibility added in this increment MUST be traceable to a current requirement. Extensibility MUST use existing library capabilities when needed, without speculative extension mechanisms or bot-specific runtime behavior. Verification MUST include a maintainer review of this requirement and User Story 2, scenario 3.

### Key Entities *(include if feature involves data)*

- **Agent configuration**: The current versioned definition of the agent to execute, containing its identity, instructions, and model selection; owned outside the core runtime.
- **Agent request**: A caller message and its permitted per-request access and correlation context.
- **Agent outcome**: The reply and completion indication, or an understandable validation or execution failure, associated with one request.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 10 valid single-message interactions in a controlled acceptance run return the expected agent reply and an explicit completion indication.
- **SC-002**: A maintainer can complete documented setup, start the service, and receive the first agent reply within 10 minutes once the documented prerequisites are available.
- **SC-003**: All acceptance cases for invalid input, invalid configuration, denied access, and unavailable external services produce understandable failures without exposing credentials or unmasked personal data.
- **SC-004**: Ten simultaneous independent interactions complete with zero cross-request message or caller-context leakage.
- **SC-005**: One supported agent-configuration change is reflected in the next request with zero runtime code edits or redeployments.
- **SC-006**: Maintainer review can locate all four core responsibilities—configuration, caller context, agent execution, and reply delivery—in the documentation and trace every added responsibility to a current requirement, with zero mechanisms introduced solely for hypothetical future features.

## Assumptions

- This feature concerns the existing `muchabo-backend/` component. The other platform components retain their established responsibilities.
- The user-requested agent-library dependency and the constitution's fixed technology decisions are binding planning inputs; this specification defines the resulting user-visible behavior.
- An existing or separately supplied configuration owner provides one valid, versioned agent configuration. Building configuration administration or its storage is outside this feature.
- The configured model gateway and execution-diagnostics destination are available as external prerequisites. This feature does not build or operate those services.
- The initial interaction is a single message and reply. Conversation history storage and cross-request conversation resumption are not required by this feature.
- Existing platform access and chat contracts apply. No new login experience or frontend functionality is requested.
- Acceptance verification may use controlled external-service substitutes so outcomes are repeatable and do not depend on live model behavior.
- Extensibility means later features build incrementally on this shared core and existing library capabilities. It does not expand the capabilities delivered in this first increment; new responsibilities are introduced only when a concrete feature requires them.
