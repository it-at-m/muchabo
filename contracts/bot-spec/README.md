# Bot specification contract v1

The admin backend owns and versions bot definitions. The runtime reads the current
definition for each interaction. The `agent` object is the supported subset of
native Pydantic AI **2.63.0** AgentSpec, inside a strict platform envelope.

`bot-spec.schema.json` is the shared Draft 2020-12 boundary schema. The generated
`native-agent-spec.schema.json` documents the complete pinned upstream format;
its extra capabilities are not accepted by this runtime increment. Fixtures are
shared producer/consumer examples, not runtime fallback configurations.

Resolve schema references only within bundled trusted contract artifacts. Never
retrieve schema URLs supplied by a bot. Enforce path/bot ID and optional agent
name equality explicitly; portable JSON Schema cannot express these relationships.

Both backends must package this directory and run the same schema/fixture checks.
See [the spec-read API](../../specs/001-core-agent-backend/contracts/bot-spec-api.md)
and [the AG-UI boundary](../../specs/001-core-agent-backend/contracts/agent-runtime.md).

## Producer/consumer handoff before live activation

- Java producer: package these exact public schema resources, validate Draft 2020-12
  with local references, and run valid/invalid fixtures plus explicit path/name
  equality checks. Implement the spec-read endpoint and its immutable-version/current
  activation semantics; the scaffold currently has no such endpoint.
- Service identity: provision a dedicated `bot-spec-reader` JWT principal. Configure
  issuer/audience validation and least-privilege read access in the producer. Existing
  example reader/writer roles are not evidence of this production policy. Operators
  own token delivery and renewal; invalid/expired tokens fail closed.
- Frontend consumer: add/use the native AG-UI client and run the shared request/event
  fixture conformance checks, including camelCase fields and exclusive terminal
  outcomes. The current frontend scaffold has no AG-UI integration.
- Activation owner: require passing bot/model evaluation and regression evidence
  before activating a spec or model change. Runtime consumer mocks are not that
  evidence and do not prove a live producer or frontend deployment.

The runtime feature supplies schemas, fixtures, bounded authenticated reads and
consumer tests. Configuration CRUD, identity issuance, frontend UI and bot evaluation
implementations remain owned by the corresponding components.

## Regenerate and verify

From `muchabo-backend/`, after updating exact pins and the lockfile together:

```bash
uv sync --frozen --group dev
uv run --frozen -m muchabo.bot_spec
uv run --frozen pytest test/test_bot_spec.py test/test_agent.py test/test_telemetry.py
```

Review the native schema diff against the supported subset before coordinating an
upgrade. `invalid-bot-specs.json` includes structural and cross-field failures; schema
consumers must explicitly check the latter rather than count structural acceptance
as complete validation. Contract-only changes trigger runtime/admin change filters.
