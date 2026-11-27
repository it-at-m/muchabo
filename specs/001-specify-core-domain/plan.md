# Implementation Plan: Admin Chatbot & MCP Configuration Data Model (As-Built)

**Branch**: `chore/try_speckit_for_database` | **Date**: 2026-11-17, revised 2026-11-27 | **Spec**: [spec.md](spec.md)

**Input**: `specs/001-specify-core-domain/spec.md`; original mandate: "Create only the documentation (plan.md and data-model.md) for the as-built state of our database schema based on the existing backend code. Do not generate any new code." Revised mandate (2026-11-27): reframe this plan as the as-built implementation plan for the feature merged in PR #29 ("Init muchabo admin"), reflecting the implemented state.

**Status**: As-built documentation phases 0 and 1 completed; plan reframed on 2026-11-27 against constitution v2.3.0.

**Feature directory**: `specs/001-specify-core-domain`.

## Summary

This plan documents the as-built implementation of the admin chatbot & MCP configuration data model as merged in PR #29. [data-model.md](data-model.md) records the state reconstructible from Flyway V001–V003: **7 application tables, 24 stored columns, 7 primary keys, 2 additional unique constraints and 5 foreign keys**.

The SQL migrations are the evidence base for the schema; the Java entities complement the object mapping and its validations. The basis is the existing source under `admin-backend/` and the domain specification together with [data-model.md](data-model.md). "As-built" here means the versioned source state, not the result of querying a running database.

The phase-0 findings and the documentation verification are integrated in this plan, matching the requested outcome scope of two documents.

## Technical Context

**Language/Version**: Java 25 per `admin-backend/pom.xml:40–45`; PostgreSQL SQL in the migrations.

**Primary Dependencies**: Spring Boot 4.1.1 (POM parent), Spring Data JPA/Hibernate, Jakarta Persistence/Validation, Flyway with PostgreSQL support and the PostgreSQL JDBC driver. Lombok supports the entity classes. Libraries without individually pinned versions are resolved via Spring Boot dependency management; their exact transitive versions are not required for the as-built description of columns and constraints.

**Storage**: PostgreSQL. `stack/docker-compose.yml:14–21` defines locally `postgres:18.4-alpine`, database `postgres` and port 5432. Migrations use unqualified table names; the actual PostgreSQL schema results from the execution environment and its `search_path`.

**Testing**: Existing Spring Boot test dependencies, JUnit/Testcontainers with PostgreSQL and ArchUnit per the POM. For this documentation outcome a static comparison of sources, specification and data model is performed. This comparison attests no executed product or integration test runs.

**Target Platform**: Server-side Spring Boot backend; `admin-backend/Dockerfile` uses a UBI10/OpenJDK-25 runtime. The local backend port is 8086 per `application-local.yml`.

**Project Type**: Administrative web service within the muchabo project. The schema of the chatbot/MCP core domain and of the isolated example entity lives in the Java admin backend.

**Performance Goals**: The examined evidence base defines no quantified database load or runtime goals. For this documentation mandate the completeness, verifiability and comprehensibility goals SC-001–005 of the specification apply.

**Constraints**: Documentation of the existing schema without new implementation. Flyway defines the schema changes; Hibernate is configured with `ddl-auto: validate`. SQL constraints, JPA mapping, Bean Validation and management behavior are reported separately.

**Scale/Scope**: 6 core entities plus `TheEntity`, 24 stored columns, 5 direct relationships, 3 versioned schema migrations and 1 repeatable test-data migration. Productive data volumes, actually applied migrations and installed server versions are not determinable from the source state and are not a prerequisite of this as-built documentation.

## Constitution Check

Basis: `.specify/memory/constitution.md`, version 2.3.0 of 2026-11-27. What is assessed is the conformity of this as-built feature and its documentation; a full runtime verification of the product is not implied. The assessment applies the **Scoped applicability** rule: a principle applies when the feature touches the surface it governs; untouched surfaces receive no preparatory scaffolding.

| Principle | Applicability and assessment (after completion of phases 0 and 1) |
| --- | --- |
| I — Simplicity First | Applies: the implementation uses plain JPA entities, two Flyway migrations and no wrappers, abstractions or options beyond the template baseline; this plan produces only alignment documents with no additional artifacts. Every artifact traces to the mandate (traceability). |
| II — Config over Code | Partially applies: the feature stores the data fields from which bot specifications can later be fed. It introduces no parallel format and changes no runtime code. |
| III — Stateless, Scalable Runtime | Not touched: no runtime logic in scope. |
| IV — Security and Data Protection by Design | Partially applies: the documented schema stores no credentials; permissions are not issued as database constraints. The example management enforces evidenced read/write roles; no permission mapping exists yet for the six core entities. |
| V — Human Oversight | Not touched: no tool execution or approval logic in scope. |
| VI — Observability | Not touched: no runtime artifacts of this feature's delta; no traces or logs in scope. |
| VII — Clean, Maintainable Code | Applies to the implemented code: typed Java entities following the template structure; the Maven build configures Spotless, PMD and SpotBugs with the findsecbugs plugin as quality gates. |
| VIII — Documentation | Core of this outcome: spec.md, data-model.md and this plan are the required artifacts; evidence paths, boundaries and validation levels are reported. |
| IX — Testing and Quality Gates | The implemented feature ships tests for the example entity management. The schema-level rules of the six core entities (uniqueness, mandatory references, length limits, delete cascades, active-flag default) are verified by `CoreDomainSchemaIntegrationTest`, added with this backport, running against the Flyway-managed schema. Documentation quality is assessed via the static source comparison in phase 1; product gates such as `mvn clean verify` are not attested by it. |
| X — Production Readiness | Partially applies: the evidenced dependencies (Spring Boot, PostgreSQL, Flyway) are established stock; no dependencies are added and no manifests or lockfiles are changed by this plan. |
| XI — User Experience | Not touched: no user interface in scope. |

**Result before and after phase 1**: Documentation gate fulfilled. All information required for the scope is clarified from local sources; missing live-instance data is named as an evidence boundary, not as an open design decision.

## Explicitly Not Built (Not Built)

Per the Development Workflow of the constitution, this plan explicitly lists what is not built:

- No product code: no entity, schema or migration changes (V001–V003 and `R__Testdata.sql` remain unchanged). The verification test `CoreDomainSchemaIntegrationTest` added with this backport is test code, not a product change.
- No management repositories, services or controllers for the six core entities.
- No package rename: the deviation of the Java base package is only documented; its fix is a separate implementation change with its own constitution alignment.
- No permission, approval, delete or runtime decisions: the as-built state is described, not assessed, extended or "improved".
- No task list (tasks.md) and no implementation run: the implemented state already exists in `main` (PR #29); this backport documents it retrospectively. Requirement-to-source traceability in spec.md replaces task coverage.

## Simplicity Review

Checked before task generation would apply: can the same documentation scope be achieved with fewer artifacts or less effort?

- The user mandate explicitly requests exactly two outcome files (plan.md with the integrated as-built analysis and data-model.md); no additional artifacts were created.
- The original five-artifact set was consolidated on 2026-11-27: source-analysis.md was merged into data-model.md (its schema sections were redundant; its unique application-behavior section became data-model.md §9) and deleted, leaving spec.md, plan.md and data-model.md as the single sources for domain rules, governance and technical evidence respectively.
- No scripts, template copies or verification tools were created for this mandate; the existing Spec Kit infrastructure is used unchanged.

## Project Structure

### Documentation (this feature)

```text
specs/001-specify-core-domain/
├── spec.md                      # As-built feature specification
├── checklists/requirements.md   # Specification review
├── plan.md                      # As-built plan with phase-0 findings
└── data-model.md                # Schema as-built state and source evidence
```

### Source Code (repository root)
```text
admin-backend/
├── pom.xml
├── Dockerfile
└── src/
    ├── main/
    │   ├── java/de/muenchen/oss/refarch/backend/
    │   │   ├── common/BaseEntity.java
    │   │   ├── chatbot/         # Chatbot, ChatbotConfig
    │   │   ├── model/           # Model
    │   │   ├── mcp/             # McpServer, McpTool, ChatbotTool
    │   │   └── theentity/       # Example entity and example management
    │   └── resources/
    │       ├── application.yml
    │       ├── application-local.yml
    │       └── db/migration/
    │           ├── schema/     # V001, V002, V003
    │           └── testdata/   # R__Testdata.sql
    └── test/java/de/muenchen/oss/refarch/backend/
stack/docker-compose.yml        # Local PostgreSQL image
```

**Structure Decision**: The documented paths correspond to the existing checkout. At the time of this revision `.specify/feature.json` no longer exists; feature resolution uses `SPECIFY_FEATURE_DIRECTORY=specs/001-specify-core-domain`. The technical as-built analysis is integrated into the two requested documents.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Existing Java base package `de.muenchen.oss.refarch.backend` instead of the constitution's `de.muenchen.oss.muchabo`. | The as-built state must name the actually existing entities and their evidence paths correctly. This justifies describing the deviation, not approving a new architecture. | Documentation under the non-existent package would be unevidenced; a package rename would be an implementation change (planned separately). |

## Phase 0 — Research and Clarified As-Built Questions

The following findings fulfil the source clarification for this documentation mandate. No new technology or integration decisions are required.

### R-001 — Schema source

- **Decision**: V001–V003 under `admin-backend/src/main/resources/db/migration/schema/` determine the reconstructible schema state.
- **Rationale**: SQL explicitly defines column types, nullability, defaults and constraints; `ddl-auto: validate` describes Hibernate's configured role as schema validator.
- **Alternatives considered**: Entity annotations alone would overlook SQL defaults and database delete cascades. Live instance state would be unevidenced without a query.

### R-002 — Validation levels and defaults

- **Decision**: Report SQL rules, JPA behavior and input validation separately.
- **Rationale**: All Java entities inherit UUID generation, but only the six core tables have an SQL UUID default. The example text minimum length 2 is Bean Validation, not an SQL constraint. `created_at` has an SQL insert default and object-side change protection, but no immutability trigger. Defaults do not replace an explicit `NULL`.
- **Alternatives considered**: A combined rule listing without level labels would claim further database guarantees.

### R-003 — Relationships and state changes

- **Decision**: Document two FK relationships with default `NO ACTION` and three FK relationships with `ON DELETE CASCADE`; additionally name the collection orphan removal as object behavior.
- **Rationale**: Chatbot and model deletion is prevented for configuration references. Configuration, tool and server deletions remove dependent assignments. `ChatbotConfig.chatbotTools` has `cascade = ALL` and `orphanRemoval = true`. The active flag belongs to the assignment, not to the tool as a whole.
- **Alternatives considered**: A blanket delete cascade or a global tool activation would be factually and technically wrong.

### R-004 — Test data and index stock

- **Decision**: Treat `R__Testdata.sql` as a configuration-dependent test-data intervention; distinguish implicit constraint indexes from explicit indexes.
- **Decision rationale**: By default only the schema folder is loaded; locally and in the Flyway Maven configuration test data is added as well. The repeatable migration empties only the example entity. The SQL contains no `CREATE INDEX`; PostgreSQL creates indexes for seven PKs and two unique constraints but not automatically for all FK columns.
- **Alternatives considered**: Presenting the five example texts as core master data, the emptying as a business rule or all foreign keys as separately indexed would be unevidenced.

## Phase 1 — Data Model and Documentation Verification

### Outcome

[data-model.md](data-model.md) contains all tables and columns with SQL type, nullability, default and Java mapping, an ER diagram, all keys and relationships as well as delete rules, state changes and validation boundaries. The migrations and their configuration context are comprehensibly described.

The already evidenced example management is application context; its roles and pagination are not SQL constraints. For the six core entities no dedicated management repositories, services or controllers are evidenced. The requirement mapping therefore refers to the existing source analysis for FR-015–016.

Closing the quality gap identified during the constitution re-validation (C1), the schema-level rules of the core entities are now verified by `CoreDomainSchemaIntegrationTest` (`src/test/java/de/muenchen/oss/refarch/backend/`), which runs against the Flyway-managed schema (`ddl-auto=validate`, migrations V001–V003) and maps to the acceptance scenarios of FR-001–012.

### Executed Static Comparison

| Check | Expected finding | Result |
| --- | --- | --- |
| Entities and tables | 7 entities ↔ 7 tables; base class without table | Fully mapped. |
| Columns | 2 + 2 + 7 + 3 + 4 + 4 + 2 = 24 | Every column described with type, nullability, default and Java attribute. |
| Keys and delete actions | 7 PKs, 2 additional unique constraints, 5 FKs; 2 without and 3 with delete cascade | Fully documented. |
| Mapping and validation | Mandatory references, inverse collection, orphan removal, timestamps, active flag and example text check | Reported separately from SQL enforcement. |
| Specification alignment | FR-001–014 and FR-017 as schema/mapping references; FR-015–016 as example management behavior | Requirement mapping included. |
| Migrations and defaults | V001–V003 plus R test data; missing SQL UUID default for the example identifier | As-built differences explicitly named. |

This comparison verifies documentation completeness and evidence fidelity. It makes no statement about passed product acceptance scenarios, an executed build or the actually applied migration state of an environment.

The whitespace check of both outcome files was successful. `check-prerequisites.sh --json --require-spec` finds the active feature, its specification, the completed plan and `data-model.md` successfully.

### Extension Hooks

At the preliminary check and the final post-hook check, `.specify/extensions.yml` does not exist. Thus no `before_plan`- or `after_plan`-hooks are registered.
