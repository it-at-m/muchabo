# Getting started

This is the starter guide for muchabo.

Add your project introduction, setup instructions, and deployment notes here.

## Initial setup after template generation

After applying the Copier template, generate and commit the lockfiles before your first Docker build:


**Python backend/job** — run `uv lock` (or `uv sync`) and commit the generated `uv.lock`.


**Vue frontend** — run `npm install` inside `muchabo-frontend/` and commit the generated `package-lock.json`.


These lockfiles are required by the Dockerfiles (`uv sync --frozen` / `npm ci`) to produce reproducible images.