# Bot Spec API Contract v1

**Producer**: Admin backend. **Consumer**: MuChaBo runtime.
**Status**: New contract design; the existing Java scaffold does not implement this endpoint.

## Read current configuration

`GET /api/v1/bots/{bot_id}/spec`

- `bot_id` follows the [data model](../data-model.md).
- Runtime supplies `Authorization: Bearer <service-access-token>` and `X-Request-ID: <server-uuid>`.
- The producer reuses its JWT resource-server authentication and requires a dedicated read-only `bot-spec-reader` service role. The existing scaffold's example reader/writer roles are not sufficient as an implicit policy.
- Service credentials are supplied externally. This increment does not build token issuance, login, or client-credentials renewal. Expired credentials fail closed; renewal is an operator/service provisioning prerequisite.
- Production JWT issuer and audience are deployment configuration; the producer must validate both. Local JWT/JWK configuration is not evidence of production identity validation.
- Every runtime request fetches one current configuration. No cache, fallback spec, conditional fetch, or direct database access.
- Runtime fetch uses a 5-second total deadline, no retry, and no redirects. Only the configured admin origin is contacted.

### Successful response

HTTP `200`, `Content-Type: application/json`, `Cache-Control: no-store`.

Body conforms to [bot-spec.schema.json](bot-spec.schema.json). See [valid example](fixtures/bot-spec.json). Maximum response body is 64 KiB. In addition to structural validation:

1. `bot_id` equals the requested path ID.
2. Optional `agent.name` equals `bot_id`.
3. `version` identifies an immutable definition: publishing a changed definition requires a different version label. A request already executing retains its loaded version; the next request sees the new current version.
4. Native AgentSpec parsing and supported-field checks agree with the shared schema. Instructions are literal text; templates and unsupported fields are rejected rather than silently ignored.
5. `authenticated` configurations are structurally valid but are denied by this anonymous-only runtime before model execution.
6. The producer activates a definition only after its validation and evaluation gates pass.

### Producer errors

| HTTP status | Meaning |
|-------------|---------|
| `401` | Missing, invalid, or expired service token. |
| `403` | Service principal lacks configuration-read permission. |
| `404` | No available active configuration for this bot. |
| `503` | Configuration service unavailable. |

Producer error bodies are not forwarded to public callers. Runtime maps `404` to its generic bot-unavailable `404`; other producer failures to sanitized `503 CONFIGURATION_UNAVAILABLE`; malformed/mismatched/oversized responses to `502 INVALID_CONFIGURATION`. No model execution occurs.

## Shared validation and packaging

Use JSON Schema Draft 2020-12 and strict JSON types. Schema references resolve only against bundled trusted artifacts, never remote schema URLs from bot data. Cross-field equality is enforced explicitly on both sides; JSON Schema alone cannot express it portably.

During implementation, publish the final schema and fixture corpus under public repository `contracts/bot-spec/`. Include the generated native AgentSpec schema for the pinned framework and describe the restricted core subset rather than creating a second agent language. Export platform constraints with Pydantic schema facilities and assert their agreement with this design contract. The Java producer consumes the same published artifact instead of maintaining another spec definition.

The Python image must package the shared artifacts: change its build context to the repository root and scope Docker COPY paths to `muchabo-backend/` plus `contracts/bot-spec/`. The admin build packages the public schema as a resource. Only schema/fixture packaging and change-filter updates are required; no cross-component private internals are accessed.

Run the same valid/invalid fixture corpus on both sides. It must include unknown fields, nulls/coercible numbers, whitespace messages, template syntax, unsupported agent capabilities, mismatched IDs/name, and unsupported schema versions. Core runtime parsing uses Pydantic and native AgentSpec; no production Python schema-validator wrapper is introduced. Schema-validation tooling may be used in contract tests and by the producer where required.

Admin endpoint implementation and identity provisioning are prerequisites owned by the admin component, outside this runtime feature. Controlled producer substitutes prove runtime behavior; producer-side contract checks must pass before live integration. This contract is additive to the scaffold API.
