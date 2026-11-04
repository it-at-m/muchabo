# Agent Runtime Contract v1

**Endpoint**: `POST /api/bots/{bot_id}/run`
**Protocol**: Native AG-UI types/events; `ag-ui-protocol==1.0.0`, Pydantic AI `2.63.0` adapter.
**Caller policy**: Anonymous public interactions only in this increment. No login UI or employee access.

## Request

Send `Content-Type: application/json` and `Accept: text/event-stream`. Use [request fixture](fixtures/agent-request.json), validated as native RunAgentInput plus the [single-message constraints](../data-model.md).

- Body limit: 64 KiB; larger payloads return `413` before execution.
- One non-whitespace user text message, at most 16,000 characters; identifiers must be UUIDs.
- `state={}`, `tools=[]`, `context=[]`; `forwardedProps` omitted or `{}`.
- No extra identity, role, instruction, context, tool, or history fields. Path ID selects a bot, never a model/provider URL.
- Callers cannot submit bot configuration. It comes solely from the admin contract.
- Explicit server-generated anonymous context has empty roles and no user identity. Incoming bearer/identity headers do not grant privileges; this endpoint never treats them as authenticated employee context.
- An `authenticated` bot configuration yields `403 ACCESS_DENIED` with zero model calls.

## Response before streaming

All responses include server-generated `X-Request-ID`. Errors have JSON `{ "code": "...", "message": "...", "request_id": "<uuid>" }` with fixed non-personal text; no raw validator/provider details.

| HTTP status | Code | Meaning |
|-------------|------|---------|
| `404` | `BOT_UNAVAILABLE` | No active configuration available. |
| `403` | `ACCESS_DENIED` | Selected configuration is not permitted anonymously. |
| `413` | `REQUEST_TOO_LARGE` | Body exceeds limit. |
| `415` | `UNSUPPORTED_MEDIA_TYPE` | Not JSON. |
| `406` | `UNSUPPORTED_RESPONSE_TYPE` | Caller does not accept SSE. |
| `422` | `INVALID_REQUEST` | Native/request-scope validation failed. |
| `502` | `INVALID_CONFIGURATION` | Producer response does not satisfy configuration contract. |
| `503` | `CONFIGURATION_UNAVAILABLE` | Configuration fetch failed, timed out, or service authentication failed. |

Existing `/` and `/api/healthz` responses remain operational probes, not agent execution; no model call or configuration fetch is required for them after valid startup configuration.

## Stream

HTTP `200`, `Content-Type: text/event-stream`, `Cache-Control: no-store`. Preserve native AG-UI encoding and camelCase fields. No custom SSE implementation or conversation-history storage.

Success includes `RUN_STARTED`, native assistant text start/content/end events, and one terminal `RUN_FINISHED`. Other native nonterminal lifecycle events may occur; consumers must not depend on a single fixed chunk count.

Execution failure ends with exactly one `RUN_ERROR` with fixed public text:

| Code | Message |
|------|---------|
| `RUN_FAILED` | `The agent could not complete your request. Please try again.` |
| `RUN_TIMEOUT` | `The agent took too long to respond. Please try again.` |

Once an error is emitted, no subsequent content or `RUN_FINISHED` is delivered. Partial content already sent is not retracted. HTTP status cannot change after stream headers are sent. Disconnects cancel and close execution rather than guarantee a terminal event over a closed connection.

### Native integration and necessary error boundary

Use `AGUIAdapter.from_request`, `run_stream`, and `streaming_response`. Native `dispatch_request` alone is insufficient: tagged adapter errors include raw exception strings and timeouts normally terminate as cancellation/`RUN_FINISHED`.

Use the supported `on_cancel` async event callback to identify `RunTimedOut`. A small request-local typed-event filter creates fresh sanitized RunErrorEvent values and suppresses later events after a terminal error, while draining/closing the native iterator. It does not implement agent execution, protocol encoding, or a new adapter class. There is no public `on_error=` callback parameter in this pinned adapter; do not invent one or subclass library event streams.

Pass native deps/metadata and `run_id` at run time; AG-UI runId is not automatically the Pydantic AI run ID. Correlation and client/provider resource contexts remain open throughout body consumption, not merely until the endpoint returns a response object.

## Bounds and verification

- Configuration fetch: 5 seconds total, zero retries.
- Model HTTP attempt: 20 seconds; native model `request_timeout`: 25 seconds including stream consumption.
- Agent run: 30 seconds; zero agent retries and zero SDK retries.
- Clients use configured origins and credentials; no provider selection from a string prefix or spec capability.
- Tests assert finite completion by these deadlines, not real-model latency targets.

Runtime contract tests parse events with native AG-UI types and assert reply text, terminal-event exclusivity, sanitized errors, cancellation cleanup, and ten concurrent request-local contexts. Consumer conformance tests use the same request/event fixtures. The existing frontend has no AG-UI client yet; frontend-side integration verification is required before live chat activation, but building that UI is outside this feature.

Trace model calls with native instrumentation, content disabled. Correlate by bot ID/version and UUID request/conversation/session identifiers. Logs and traces exclude personal content and secrets, including failure payloads. Frontend request IDs are correlation only; they are never authorization inputs.
