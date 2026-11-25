# AGENTS.md

Guidance for coding agents working in this repository. The project's agent tooling is
opencode; Spec Kit is integrated for opencode only.

## Binding rules

The [MuChaBo constitution](.specify/memory/constitution.md) takes precedence over all other
guidance, including this file. Read it before planning or changing code. This file only
summarises the rules agents most often get wrong.

## Most important rules

- **Simple, never sloppy.** Use the least machinery that fully meets the specification. Do not
  lower quality (validation at boundaries, error handling, security, tests, docs) to save
  code, and do not add layers, abstractions, wrappers, options, or scaffolding in the name of
  quality or future needs. Everything you add must trace to a current requirement.
- **Built-ins first.** Use Pydantic AI, FastAPI, Spring Boot, Vue, and AG-UI features before
  writing custom code. No wrappers around core libraries.
- **One source of truth.** Shared contracts live only in [`contracts/`](contracts/). Link to
  them; never copy them into specs or components.
- **Config over code.** No bot-specific code in the runtime or chat frontend; bots are defined
  by their bot spec.
- **Python only through uv.** Use `uv sync --frozen` and `uv run --frozen ...`. Never use bare
  `python`, `pip`, or standalone tool invocations.

## Repository map

| Path | Part |
|------|------|
| `admin-frontend/` | Admin UI for bot specs (Vue 3, TypeScript) |
| `admin-backend/` | Stores, validates, and serves bot specs (Java, Spring Boot, Maven) |
| `muchabo-backend/` | Shared agent runtime (Python, FastAPI, Pydantic AI, uv) |
| `muchabo-frontend/`, `webcomponent/` | Chat UI over AG-UI (Vue 3, TypeScript) |
| `contracts/` | Shared public interface schemas and fixtures |
| `specs/` | Spec Kit feature specs, plans, and tasks |

Parts communicate only through documented interfaces (bot spec API, AG-UI).

## Workflow

Features follow Spec Kit through the opencode commands in `.opencode/commands/`:
`/speckit.specify` → `/speckit.clarify` → `/speckit.plan` → `/speckit.tasks` →
`/speckit.analyze` → `/speckit.implement`. Each feature lives in `specs/NNN-name/`.
Check every spec, plan, and change against the constitution.

Do not commit, push, or change branches unless explicitly asked.
