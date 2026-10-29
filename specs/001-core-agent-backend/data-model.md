# Data Model: Minimal Core Agent Backend

**Date**: 2026-10-29
**Scope**: Request-local values only. No database, conversation store, or configuration cache.

## Bot configuration

The admin backend returns one configuration envelope. Its `agent` member uses the native Pydantic AI AgentSpec format, restricted to the fields this increment serves.

| Field | Type | Rules |
|-------|------|-------|
| `schema_version` | String | Exactly `"1"`; reject numbers, booleans, and coercion. Contract version, distinct from bot version. |
| `bot_id` | String | 1–64 characters; `^[a-z0-9][a-z0-9_-]*$`; must equal the requested path identifier. |
| `version` | String | 1–64 characters; same identifier pattern; immutable label for this bot definition. |
| `access_policy` | String | `anonymous` or `authenticated`; the current runtime executes only `anonymous`. |
| `agent` | Native AgentSpec | Required `model` and `instructions`; optional `name`; other keys rejected in this increment. |
| `agent.model` | String | Non-whitespace, 1–128 characters; gateway alias, never a credential or caller-selected URL. |
| `agent.instructions` | String | Non-whitespace, 1–16,000 characters; literal instructions. Template syntax is rejected in this increment. |
| `agent.name` | String | Optional, same identifier restrictions as `bot_id`; if present, equal to `bot_id`. Runtime uses `bot_id` as its non-personal agent name. |

The strict platform envelope contains a native AgentSpec, not a replacement agent model. Minimal boundary checks reject unsupported raw keys before native parsing so AgentSpec's permissive defaults cannot discard them silently. Export matching JSON Schema constraints with Pydantic's schema facilities; parity tests must cover checks not inferred automatically from validators. The [schema](contracts/bot-spec.schema.json) is the design contract for the supported native subset.

No `capabilities`, `model_settings`, `metadata`, output/dependency schemas, external schema URLs, tools, or credentials are accepted from configuration in this increment. Library defaults for those fields must not enable unsupported behavior. Model routing, retry/time limits, and instrumentation are enforced by the runtime. Later supported native fields require a coordinated contract change and tests.

## Agent request

Use AG-UI `RunAgentInput`, not a custom chat request class. See [AG-UI contract](contracts/agent-runtime.md).

| Field | Rules |
|-------|-------|
| Path `bot_id` | Same identifier rules as configuration. |
| `threadId`, `runId` | UUID strings; correlation inputs only, never evidence of identity or stored history. |
| `messages` | Exactly one user message with UUID `id` and a string `content` containing non-whitespace; maximum 16,000 characters. |
| `state` | Exactly `{}`. |
| `tools`, `context` | Exactly `[]`. |
| `forwardedProps` | Omitted or exactly `{}`. |

Reject system/assistant/tool messages, multimodal content, message extras, nonempty state, frontend tools/context, forwarded instructions, and unsupported top-level fields. Do not normalize an invalid message into valid content or include offending values in errors.

## Caller context

A fresh typed dataclass is passed through native agent dependencies for every request.

| Attribute | Source / meaning |
|-----------|------------------|
| `access_policy` | Server-set `anonymous`; no employee authentication inferred. |
| `user_id` | `None`; no personal identity captured. |
| `tenant` | Server-set `public` for this increment; no internal tenant access. |
| `roles` | Empty tuple; cannot be supplied or elevated by the caller or bot configuration. |
| `request_id` | Server-generated UUID; returned as `X-Request-ID`. |
| `conversation_id` | Validated AG-UI `threadId`; no persistence/resumption semantics. |
| `session_id` | Same opaque UUID as `conversation_id` for this single-interaction scope. |

The runtime service credential used to read configuration is separate from caller context and never becomes caller permissions. No incoming identity/role headers or body fields are trusted. Authenticated configurations are rejected before model execution.

## Outcome and lifecycle

```text
request received → body validated → configuration fetched/validated
                 → access allowed → agent running → reply completed
                                      └──────────→ run failed/timed out
```

- Validation, access, and configuration failures before streaming produce sanitized HTTP errors and make zero model calls.
- Successful runs emit native AG-UI message events and one `RUN_FINISHED`.
- Execution failures and timeouts emit one sanitized terminal `RUN_ERROR`; no success event follows it.
- A disconnect cancels execution and closes stream resources; no delivery guarantee is possible after disconnect.
- All request values and per-request agents are released when stream consumption ends. Only stateless HTTP clients and telemetry infrastructure are application-scoped.

## Diagnostic record

Allow only static event/error codes, server request ID, validated UUID conversation/session IDs, bot ID/version, model alias, elapsed time, and available token/cost counts. No prompts, replies, configuration bodies, URLs containing secrets, bearer credentials, personal identity, raw exceptions, or stack traces are emitted. Trace attributes use a fixed allowlist; source-side instrumentation disables message and binary content. These restrictions cover rejected requests as well as executed runs.
