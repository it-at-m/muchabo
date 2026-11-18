# muchabo Constitution

## Core Principles

### I. RefArch System Topology (Admin & Public Split)
- The application strictly follows the [it@M Reference Architecture (RefArch)](https://muenchen.de) and separates internal administration from public citizen-facing interfaces:
  - **Admin Interface (`admin-frontend/`):** Internal SPA for staff/administrators behind Keycloak SSO.
  - **Public Interface (`webcomponent/`):** Embeddable Micro Frontend for Munich web portals (e.g. muenchen.de) using Munich PatternLab.
  - **Backend (`admin-backend/`):** Spring Boot service serving both internal admin APIs and public endpoints.
- All external traffic MUST route through the `refarch-gateway` (Default local port: `8083`). Direct exposure of backend services is forbidden.

### II. Backend Standards (Spring Boot & PostgreSQL)
- **Framework & Runtime:** Java with **Spring Boot** (Default local port: `8086`) under base package `de.muenchen.oss.muchabo`.
- **Admin vs. Public API Separation:** Separate administrative controllers/services from public citizen-facing controllers. Document all endpoints via OpenAPI.
- **Persistence & Migrations:** Use **PostgreSQL** (`5432`) as the primary database. All schema changes MUST use versioned **Flyway** SQL migrations (`mvn flyway:migrate`).

### III. Frontend Standards (Admin SPA vs. Public Web Component)
- **Shared Core:** Both UIs use **TypeScript**, **Vue.js** (strictly Composition API with `<script setup lang="ts">`), **Vite**, and **VueI18n** (ISO-639-1 JSON files in `locales/`, German `de` mandatory default).
- **Admin Frontend (`admin-frontend/`, Port `8081`):** MUST use **Vuetify** (via Vuetify Vite Plugin auto-imports; no manual Vuetify component imports in `<script>`). Do NOT use PatternLab components here.
- **Public Web Component (`webcomponent/`, Port `8082`):** MUST use **`@muenchen/muc-patternlab-vue`** to match the official City of Munich corporate design. Do NOT use Vuetify in the public web component.

### IV. Security & Authentication
- **Admin Endpoints & Routes:** Protected via **Keycloak** OAuth 2.0 / OIDC (Port `8100`) and role-based access control (`@PreAuthorize`). Gateway-to-backend traffic MUST pass validated **JWTs**.
- **Public Endpoints & Routes:** Unauthenticated endpoints for the public web component MUST reside under `/public/**` (or `refarch.security.public-patterns`) with strict input validation and rate-limiting considerations. Keep CSRF protection enabled unless explicitly whitelisted via `refarch.security.csrf-whitelisted`.

### V. Automated Quality Gates & Testing
- **Backend:** Must pass `mvn clean verify` (**Spotless**, **PMD**, **SpotBugs**, **find-sec-bugs**).
- **Frontends (`admin-frontend/` & `webcomponent/`):** Must pass **ESLint**, **Prettier**, `vue-tsc`, and **Vitest** (`npm run test`).
- **Supply Chain:** Maintain CycloneDX SBOM generation and zero unresolved **Trivy** vulnerabilities.

## Local Development & Infrastructure
- Support Spring profiles `local` (with `stack/` Docker Compose) and `no-security` (isolated local development).

## Governance
- This constitution governs all `/speckit.specify`, `/speckit.plan`, and `/speckit.analyze` workflows.
- Any architectural deviation requires amending this file before implementation.

**Version**: 1.0.0 | **Ratified**: 2026-11-17 | **Last Amended**: 2026-11-17
