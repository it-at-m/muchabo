FROM registry.access.redhat.com/ubi10/ubi-minimal:10.1-1775622738

COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /uvx /bin/

ENV UV_PROJECT_ENVIRONMENT=/app/muchabo/.venv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app/muchabo

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY . /app/muchabo/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ARG IMAGE_CREATED="unknown"
ARG IMAGE_REVISION="unknown"
ARG IMAGE_VERSION="unknown"
LABEL org.opencontainers.image.authors="Landeshauptstadt München <opensource@muenchen.de>" \
    org.opencontainers.image.vendor="Landeshauptstadt München" \
    org.opencontainers.image.created="$IMAGE_CREATED" \
    org.opencontainers.image.revision="$IMAGE_REVISION" \
    org.opencontainers.image.version="$IMAGE_VERSION" \
    org.opencontainers.image.url="https://github.com/it-at-m/muchabo" \
    org.opencontainers.image.documentation="https://github.com/it-at-m/muchabo/README.md" \
    org.opencontainers.image.source="https://github.com/it-at-m/muchabo" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.title="muchabo-backend" \
    org.opencontainers.image.description="Python backend for Munich Chatbot Framework & Platform"

ENV PATH="/app/muchabo/.venv/bin:$PATH"

RUN useradd -r -u 1001 -g root appuser && chown -R appuser /app

USER appuser

ENTRYPOINT ["/app/muchabo/.venv/bin/python", "main.py"]
