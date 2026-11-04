FROM registry.access.redhat.com/ubi10/ubi-minimal:10.1@sha256:5af8e51abe2a81b4247f05219284a627d37fb9ccf1055b90528a246fac11bc4d

COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /uvx /bin/

ENV UV_PROJECT_ENVIRONMENT=/app/muchabo/.venv
ENV UV_PYTHON_INSTALL_DIR=/opt/python
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app/muchabo

COPY muchabo-backend/pyproject.toml muchabo-backend/uv.lock muchabo-backend/.python-version ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY muchabo-backend/ /app/muchabo/
COPY contracts/bot-spec/ /app/contracts/bot-spec/

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

RUN microdnf install -y shadow-utils && microdnf clean all && \
    useradd -r -m -u 1001 -g root appuser && chown -R appuser /app

USER appuser

ENTRYPOINT ["uv", "run", "--frozen", "--no-dev", "python", "main.py"]
