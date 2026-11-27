# Feature Specification: Admin Chatbot & MCP Configuration Data Model

**Feature Branch**: `chore/try_speckit_for_database`

**Created**: 2026-11-17

**Revised**: 2026-11-27 (reframed as the as-built feature specification for PR #29; translated to English)

**Status**: Retrospective, as-built specification. The feature described here is implemented and merged into `main` via PR #29 ("Init muchabo admin"). Requirements describe behavior that holds in the current source state; they are not an announcement of future work.

**Input**: Original user description (2026-11-17): "Analyse our existing data model in `admin-backend/src/main/java/de/muenchen/oss/muchabo/` (entities, repositories) as well as the Flyway migrations in `admin-backend/src/main/resources/db/migration/`. Derive from it retrospectively the domain specification (spec.md) for our core domain, including all entities, relationships and validation rules." Revised mandate (2026-11-27): reframe this document as the Spec Kit feature specification for PR #29, reflecting the implemented state. The requested Java path did not exist; the actual paths and every source reference are recorded in [data-model.md](data-model.md).

## User Scenarios & Testing *(mandatory)*

The scenarios describe domain-valid data and changes as they hold in the implemented schema. They do not attest an operable chatbot administration: management functions are only evidenced for the isolated example entity. The technical derivation is recorded in [data-model.md](data-model.md).

### User Story 1 - Distinguish chatbots, models and configurations (Priority: P1)

As a data steward, I want to distinguish chatbots, their configurations and the associated models unambiguously and understand the stored settings.

**Why this priority**: Chatbot, model and configuration form the foundation of the domain description of chatbot behavior.

**Independent Test**: One chatbot, one model and two configurations suffice to verify identity, mandatory fields, multiple configurations and version labels.

**Acceptance Scenarios**:

1. **Given** a chatbot and a model with existing names of up to 100 characters, **When** a configuration with an existing prompt, a numeric temperature and a version label of up to 20 characters is stored, **Then** it has its own identifier, exactly this chatbot, exactly this model and an automatically set creation timestamp (FR-001–004).
2. **Given** an existing configuration, **When** another configuration with the same model and the same version label is stored for the same chatbot, **Then** a separate record is permitted; the version label is not unique (FR-005).
3. **Given** a configuration, **When** a mandatory field is missing or a reference to a non-existent chatbot or a non-existent model is set, **Then** that data state is not permitted (FR-003, FR-012).
4. **Given** an existing configuration, **When** the prompt or temperature is changed regularly, **Then** its creation timestamp is preserved; a general immutability of the configuration is not mandated (FR-004–005).
5. **Given** a model named "Model A", **When** another model with exactly the same name is stored, **Then** the duplicate model name is not permitted; identically named chatbots are permitted (FR-002).

---

### User Story 2 - Assign tools per configuration (Priority: P2)

As a data steward, I want to record which tools of an MCP server are assigned to a configuration and whether they are active or inactive there. An MCP server is a provider of such tools.

**Why this priority**: The assignment describes capabilities per configuration without deriving a global activation of a tool from it.

**Independent Test**: One server, one tool and two prepared configurations allow verifying mandatory reference, multiple use, uniqueness and the independent active flag.

**Acceptance Scenarios**:

1. **Given** an existing server, a tool assigned to it and an existing configuration, **When** the tool and the configuration are assigned to each other for the first time, **Then** the assignment receives its own identifier and is active unless stated otherwise (FR-001, FR-006–008).
2. **Given** an existing assignment, **When** the same tool is assigned to the same configuration again, **Then** the duplicate assignment is not permitted, regardless of the active flag (FR-009).
3. **Given** a tool with active assignments in two configurations, **When** one assignment is deactivated, **Then** the other remains active; neither the tool nor the deactivated assignment is deleted (FR-008–009).
4. **Given** a server with valid mandatory fields, **When** two tools with the same name and no description are stored, **Then** both are permitted and each is assigned to exactly this server (FR-006–007).
5. **Given** a server or a tool, **When** a mandatory field is missing, a name is 101 characters long, a server address is 256 characters long or a tool references a non-existent server, **Then** the affected data state is not permitted; an existing address text of up to 255 characters is not subject to any evidenced format check (FR-006–007, FR-012–013).

---

### User Story 3 - Understand delete consequences for dependent data (Priority: P2)

As a data steward, I want to know which records are preserved or removed when a deletion occurs and which relationships prevent a deletion.

**Why this priority**: These rules protect the assignment of configurations and prevent orphaned tool assignments.

**Independent Test**: Prepared records with the five described relationships allow every deletion check independently of a chatbot conversation.

**Acceptance Scenarios**:

1. **Given** a chatbot or model with at least one configuration, **When** the chatbot or the model is to be deleted, **Then** the existing configuration prevents the deletion (FR-010).
2. **Given** a configuration with tool assignments, **When** the configuration is deleted, **Then** its assignments are removed; chatbot, model, tools and servers remain (FR-011).
3. **Given** a tool with assignments in several configurations, **When** the tool is deleted, **Then** all of its assignments are removed; the configurations and the server remain (FR-011).
4. **Given** a server with tools and their assignments, **When** the server is deleted, **Then** its tools and their assignments are removed; affected configurations and chatbots remain (FR-011).
5. **Given** a tool assignment within a configuration, **When** this assignment is removed from the configuration, **Then** only the assignment is removed; tool and configuration remain (FR-011).
6. **Given** a chatbot or model without a configuration, **When** this record is deleted, **Then** none of the described relationships prevents its deletion (FR-010).

---

### User Story 4 - Classify the existing example management (Priority: P3)

As a data steward, I want to know the isolated example entity and its evidenced rules without attributing an unevidenced significance to it in the chatbot core domain.

**Why this priority**: The as-built description must cover all existing entities and make their domain boundaries comprehensible.

**Independent Test**: One example record and persons with read or write permission suffice for the independent check.

**Acceptance Scenarios**:

1. **Given** a person with write permission, **When** an example text of 2 or 8 characters is stored, **Then** it is permitted and receives an identifier; a missing text and texts of 1 or 9 characters are not permitted in the example management (FR-001, FR-014–015).
2. **Given** a person with read permission, **When** they read single or paginated example records, **Then** this is allowed; creating, changing and deleting require write permission (FR-015).
3. **Given** a person with write permission and an example record, **When** they change its text validly and then delete it, **Then** the change preserves the identifier and after the deletion the record is gone (FR-015).
4. **Given** a non-existent example identifier, **When** the record is read or changed, **Then** "not found" is reported (FR-016).
5. **Given** eleven example records, **When** they are read paginated without further parameters, **Then** the first page contains ten records; negative page numbers and non-positive page sizes are not permitted (FR-016).

### Edge Cases

- **Missing and empty**: A mandatory text must not be missing. For the six core entities, empty texts and pure whitespace are however not excluded. The example text may consist of whitespace but must satisfy the length 2–8 in the example management.
- **Boundary lengths**: Names of up to 100 characters, server addresses of up to 255 characters and version labels of up to 20 characters are within their limits; one additional character exceeds each of them. For prompt and tool description no domain-level maximum length is defined.
- **Empty model name**: An empty model name is possible; a second identical empty model name violates uniqueness. Equating differently spelled names is not defined at domain level.
- **Temperature**: There is no defined default value and no evidenced minimum/maximum; ordinary values such as −1 or 3 are not excluded by a range rule. Non-finite special values are not specified as a domain guarantee.
- **Multiple configurations**: Even the same chatbot may have multiple configurations with the same model and the same version label. The label determines neither an ordering nor a current or released configuration.
- **Optional assignments**: A chatbot may exist without a configuration; a configuration without tools, a server without tools and a tool without a configuration assignment are equally permitted.
- **Inactive duplicate assignment**: An inactive assignment remains in place and prevents a second assignment of the same configuration/tool pair.
- **Server deletion**: The deletion may affect assignments in several chatbots but removes none of those configurations or chatbots.
- **Missing description**: A missing and an empty tool description are both permitted but are different values.
- **Unknown example identifier on deletion**: The explicitly evidenced not-found rule for read and change is not defined identically for deletion.

## Requirements *(mandatory)*

### Functional Requirements

The requirements state the evidenced as-built rules. "Existing" means that a value is not missing; for texts it does not automatically mean "not empty".

- **FR-001 — Identity**: Every record of the seven entity kinds MUST have its own identifier that is unique within its entity kind and is assigned automatically on regular creation. Tool assignments are independently identifiable records.
- **FR-002 — Chatbot and model**: Chatbot name and model name MUST exist and must be at most 100 characters long. Model names MUST be unique; exactly equal model names are not permitted. Chatbot names need not be unique.
- **FR-003 — Configuration**: Every configuration MUST be assigned to exactly one existing chatbot and exactly one existing model. Prompt, numeric temperature value and version label MUST exist; the version label must be at most 20 characters long.
- **FR-004 — Creation timestamp**: Every configuration MUST have an automatically set creation timestamp as a time zone-aware point in time. Regular changes preserve it. No guarantee follows that the originally used time zone name is preserved.
- **FR-005 — Configuration variety**: A chatbot MUST be representable with 0..n configurations. The same model and the same version label may be used multiple times, including for the same chatbot. Versions do not determine any evidenced ordering, immutability or current selection.
- **FR-006 — MCP server**: Every server MUST have an existing name of up to 100 characters and an existing address text of up to 255 characters. Neither value needs to be unique. A server may have 0..n tools.
- **FR-007 — MCP tool**: Every tool MUST be assigned to exactly one existing server and have an existing name of up to 100 characters. The description is optional. Tool names need not be unique globally or within the same server.
- **FR-008 — Tool activation**: Every tool assignment MUST have exactly one existing configuration, exactly one existing tool and an active flag (active/inactive). New assignments are active by default. The flag applies solely to the individual assignment; deactivating deletes neither the tool nor the assignment.
- **FR-009 — Assignment uniqueness**: Per configuration and tool, at most one assignment may exist, regardless of its active flag. A configuration may use 0..n different tools; a tool may be assigned to 0..n different configurations.
- **FR-010 — Deletion barriers**: A chatbot or model must not be deleted while a configuration references it. Without such references, the deletion is not restricted by any of the described relationships.
- **FR-011 — Dependent deletions**: Deleting a configuration MUST remove its tool assignments. Deleting a tool MUST remove all associated assignments. Deleting a server MUST remove its tools and thereby their assignments. Removing an assignment from a configuration MUST remove that assignment. All other records remain according to the relationship table.
- **FR-012 — Valid data states**: Missing mandatory values, missing or non-existent mandatory references, exceeded length limits and the two described uniqueness violations are not permitted. A dependent record MUST reference exactly the existing parent object named in the relationship table.
- **FR-013 — As-built limits**: For the core entities no minimum text length, no exclusion of pure whitespace, no address format check, no temperature range and no version format are evidenced. For prompt and tool description no domain-level maximum length is defined. Additional rules must not be presented as already existing business rules.
- **FR-014 — Example text**: An example record MUST have an existing text of at most 8 characters. The example management additionally enforces the minimum length 2; text uniqueness and exclusion of pure whitespace are not mandated. The lower bound is not enforced equally at every storage level.
- **FR-015 — Example management**: Create, read, paginated read, change and delete are evidenced for the example entity. Read or write permission suffices for reading; create, change and delete require write permission. Regularly changing the text MUST preserve the identifier.
- **FR-016 — Example lookup and pages**: Reading or changing an unknown example identifier MUST report "not found". Without further parameters, paginated display starts at page 0 with up to 10 records. Page numbers MUST be non-negative and page sizes positive. A fixed ordering or domain-level maximum page size is not evidenced.
- **FR-017 — Documentation completeness**: This specification MUST describe all seven entities, all their attributes including identifiers, all five direct relationships and the evidenced validations and delete rules. Acceptance: comparison against the source inventory without a missing attribute, missing relationship or unevidenced added business rule.

### Implementation Traceability (as-built)

The feature is implemented in `admin-backend/` as merged by PR #29. Each requirement maps to its implementing sources; detailed line references are in [data-model.md](data-model.md).

| Requirements | Implementing sources |
| --- | --- |
| FR-001 | `common/BaseEntity.java` (UUID identity for all entities); UUID primary keys in all migrations |
| FR-002 | `chatbot/Chatbot.java`, `model/Model.java`; `schema/V002__Project_Init.sql` (name columns, model name UNIQUE) |
| FR-003 | `chatbot/ChatbotConfig.java`; `schema/V002__Project_Init.sql` (mandatory FKs, prompt, temperature, version) |
| FR-004 | `ChatbotConfig.java` (`@CreationTimestamp`, `updatable = false`); `created_at` default in V002 |
| FR-005 | `ChatbotConfig.java`; absence of a uniqueness rule on (chatbot, version) in V002 |
| FR-006 | `mcp/McpServer.java`; `schema/V003__Add_MCP.sql` |
| FR-007 | `mcp/McpTool.java`; `schema/V003__Add_MCP.sql` (mandatory server FK) |
| FR-008 | `mcp/ChatbotTool.java`; `schema/V003__Add_MCP.sql` (`is_active` default `TRUE`) |
| FR-009 | `uq_chatbot_config_tool` in V003 and `@Table` constraint in `ChatbotTool.java` |
| FR-010 | `fk_chatbot_config_chatbot`, `fk_chatbot_config_model` with `NO ACTION` in V002 |
| FR-011 | `fk_mcp_tool_server`, `fk_chatbot_tool_config`, `fk_chatbot_tool_tool` with `CASCADE` in V003; `orphanRemoval = true` on `ChatbotConfig.chatbotTools` |
| FR-012 | `NOT NULL` columns and mandatory foreign keys across V002/V003 |
| FR-013 | Absence of `CHECK` constraints and of Bean Validation on the core entities (negative evidence, see data-model.md) |
| FR-014–016 | `theentity/TheEntity.java`, `theentity/dto/TheEntityRequestDTO.java`, `TheEntityController.java`, `TheEntityService.java`, `security/Authorities.java`; `schema/V001__TheEntity_schema.sql` |
| FR-017 | This specification together with [data-model.md](data-model.md) |

Schema-level rules (FR-001–012) are additionally verified by `admin-backend/src/test/java/de/muenchen/oss/refarch/backend/CoreDomainSchemaIntegrationTest`, which runs against the Flyway-managed schema (V001–V003).

### Key Entities *(include if feature involves data)*

Each entity owns, in addition to the domain attributes listed below, its own identifier (`id`) per FR-001. The names in parentheses enable the as-built comparison without prescribing an implementation.

| Entity | Domain meaning | Full domain attributes and rules |
| --- | --- | --- |
| Chatbot (`Chatbot`) | Named chatbot with separately managed settings. | Name (`name`): existing, at most 100 characters, not necessarily unique. |
| Model (`Model`) | Reusable AI model identified by name. | Model name (`modelName`): existing, at most 100 characters, unique. |
| Configuration (`ChatbotConfig`) | Settings of a specific chatbot including model reference. | Chatbot (`chatbot`): exactly one, existing. Model (`model`): exactly one, existing. Prompt (`prompt`): existing text without a defined domain-level maximum length. Temperature (`temperature`): existing numeric value, without a defined range or default. Version label (`version`): existing, at most 20 characters, not unique. Creation timestamp (`createdAt`): existing, automatically set, preserved on regular change, time zone-aware. Tool assignments (`chatbotTools`): 0..n, initially empty, without an evidenced ordering. |
| MCP server (`McpServer`) | Provider of tools. | Name (`name`): existing, at most 100 characters. Address (`url`): existing text, at most 255 characters. Neither necessarily unique; no evidenced address format check. |
| MCP tool (`McpTool`) | Named capability of a specific server. | Server (`mcpServer`): exactly one, existing. Name (`name`): existing, at most 100 characters, not necessarily unique. Description (`description`): optional text without a defined domain-level maximum length. |
| Tool assignment (`ChatbotTool`) | Connection of configuration and tool with a configuration-scoped active flag. | Configuration (`chatbotConfig`): exactly one, existing. Tool (`mcpTool`): exactly one, existing. Active flag (`isActive`): existing, active/inactive, active by default. The combination of configuration and tool is unique. |
| Example record (`TheEntity`) | Isolated example record without an evidenced meaning in the chatbot domain. | Text (`textAttribute`): existing, stored with at most 8 characters; in the example management additionally minimum length 2, not necessarily unique. No relationships to the other entities. |

The shared identifier is an identity property, not an additional domain entity. The collection of tool assignments is a relationship, not an additional data object.

#### Relationships and Lifecycle

| Parent object | Dependent object | Cardinality and mandatory reference | Consequence of deleting the parent object |
| --- | --- | --- | --- |
| Chatbot | Configuration | Chatbot has 0..n configurations; each configuration exactly 1 chatbot. | Prevented while a configuration references it. |
| Model | Configuration | Model has 0..n configurations; each configuration exactly 1 model. | Prevented while a configuration references it. |
| MCP server | MCP tool | Server has 0..n tools; each tool exactly 1 server. | Tools and their tool assignments are removed; configurations remain. |
| Configuration | Tool assignment | Configuration has 0..n assignments; each assignment exactly 1 configuration. | Assignments are removed; tools, servers, chatbot and model remain. |
| MCP tool | Tool assignment | Tool has 0..n assignments; each assignment exactly 1 tool. | Assignments are removed; configurations and servers remain. |

These five direct relationships mediate an n:m relationship between configuration and tool that is optional on both sides. Deleting an assignment removes neither its tool nor its configuration. Removing a dependent record does not delete a parent object.

#### Validation Matrix

| Rule group | Scope | Permitted | Not permitted or not defined |
| --- | --- | --- | --- |
| Identity | All seven entities | Own assigned identifier per record. | Missing identifier or duplicate within an entity kind. |
| Mandatory name and length | Chatbot, model, server, tool | Existing name of up to 100 characters, including empty. | Missing name or more than 100 characters. |
| Server address | Server | Existing address text of up to 255 characters, including empty. | Missing value or more than 255 characters; no additional format check evidenced. |
| Prompt | Configuration | Existing text, including empty. | Missing value; no domain-level maximum length evidenced. |
| Temperature | Configuration | Existing numeric value. | Missing value; range, default and domain-level special-value behavior not defined. |
| Version label | Configuration | Existing text of up to 20 characters, including empty or used multiple times. | Missing value or more than 20 characters; format and uniqueness not defined. |
| Creation timestamp | Configuration | Automatically set timestamp, preserved on regular change. | Missing timestamp; regular changes must not replace it. |
| Description | Tool | Missing or existing text, including empty. | No additional domain-level length or content rule evidenced. |
| Mandatory relationship | Five direct relationships | Exactly one existing parent object per dependent record. | Missing reference or non-existent target. |
| Model name uniqueness | Model | Different names. | Exactly equal names, including two empty names; further name normalization not defined. |
| Assignment uniqueness | Tool assignment | Different configuration/tool pairs. | Same pair multiple times, regardless of the active flag. |
| Active flag | Tool assignment | Active/inactive; active unless stated otherwise. | Missing flag of an existing record. |
| Example text | Example record and example management | Stored existing text of up to 8 characters; in the example management additionally at least 2. Pure whitespace within these limits is permitted. | Missing text or more than 8 characters; in the example management additionally less than 2. Minimum length not enforced at every storage level. |
| Example permission | Example management | Read with read or write permission; changes with write permission. | Changes without write permission; no transfer to the core entities evidenced. |
| Example pages | Example management | Page number from 0, size from 1; default first page, size 10. | Negative page number or non-positive size; fixed ordering and maximum size not defined. |

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 — Completeness**: 100 % of the six core entities and the one example entity, their attributes and the five direct relationships are described; the as-built comparison leaves no element unmapped.
- **SC-002 — Verifiability**: For each of the 15 rule groups, a person reviewing the domain can distinguish permitted, not-permitted and not-defined cases from this specification. All 17 requirements have acceptance scenarios or an explicitly named completeness comparison.
- **SC-003 — Delete consequences**: For all five direct relationships and for removing a single tool assignment, the preserved and removed records or deletion barriers are determinable without additional assumptions.
- **SC-004 — Comprehensibility**: In a domain acceptance review, two responsible persons can independently explain all four flows and justify the outcomes of the 21 acceptance scenarios consistently; no contradictory rule interpretation remains open.
- **SC-005 — As-built fidelity**: In the review against the source inventory there are zero unevidenced added mandatory validations, version selection rules or claims of already operable core management functions.

The success criteria assess this specification against the implemented state. New runtime, load or usability targets for the product are not derived from the as-built state. The domain acceptance by two persons is a verifiable goal, not an already executed proof.

## Assumptions

- **Evidence base**: The authoritative basis is the versioned source state as of 2026-11-27 (identical to `main` since PR #29), not the inspected state of a running database. The Java model lives under a base package deviating from the constitution; the actual paths and individual evidence are in [data-model.md](data-model.md).
- **Scope**: The core domain comprises chatbots and their configurations, the model catalogue as well as MCP servers, tools and assignments. The isolated example record is included for completeness. Conversations, messages, user profiles, knowledge sources, tenants, billing and publication/release status are not defined as separate domain data objects in the examined evidence base.
- **Actors and principles**: "Data steward" is the assumed perspective for describing the data model, not an evidenced concrete permission role of the core entities. The project principles separate internal administration and public use; a concrete permission mapping for the six core entities is not derivable from the model. The evidenced read/write roles concern the example management.
- **Operability**: The scenarios state valid as-built data and changes. Dedicated management functions or domain search rules for the six core entities are not evidenced. An active tool assignment guarantees neither execution nor reachability of the server or availability of the model.
- **Dependencies**: Configurations require existing chatbots and models; tools require existing servers; assignments require existing configurations and tools. Otherwise the participants can exist without dependent records.
- **Validation levels**: The rule description is not a promise of early input validation or specific error messages for the core entities. The example management additionally checks its minimum text length on input; storage does not enforce this lower bound everywhere. The creation timestamp is preserved on regular configuration changes; protection against changes via every possible storage access is not evidenced. The technical distinction is in the source analysis.
- **Text length**: Boundary-case checks refer to ordinary letters. A uniform counting of visible characters across all Unicode special characters is not derivable from the existing rules.
- **Version and status**: The version label is freely assigned, without an evidenced format or selection rule. Activation concerns only the tool assignment. Further archiving/release processes, retention periods, domain-level sortings or name normalizations are not defined for lack of evidence.
- **Governance**: The project constitution (v2.3.0, 2026-11-27) and the actual Java base package deviate from each other: the constitution names `de.muenchen.oss.muchabo`, the implemented code uses `de.muenchen.oss.refarch.backend`. This specification records the as-built state; the fix is a separate package rename change with its own constitution alignment, not part of this feature. The deviation is concretely named in the source analysis.
