FROM node:22.22.2-alpine AS builder

WORKDIR /build

COPY package.json package-lock.json ./

RUN npm ci

COPY index.html tsconfig.json tsconfig.app.json tsconfig.node.json vite.config.ts ./
COPY src ./src
COPY docker ./docker

RUN npm run build

FROM registry.access.redhat.com/ubi10/nginx-126:10.1-1775622738

COPY --from=builder /build/dist /opt/app-root/src
COPY docker/nginx/default.conf "${NGINX_DEFAULT_CONF_PATH}"

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
    org.opencontainers.image.title="muchabo-frontend" \
    org.opencontainers.image.description="Vue frontend for Munich Chatbot Framework & Platform"

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
