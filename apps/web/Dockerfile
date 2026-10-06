# syntax=docker/dockerfile:1.7

ARG NODE_IMAGE=node:24-alpine
ARG NGINX_IMAGE=nginx:1.29-alpine

# The Vite output is architecture-independent static content. Running the
# dependency/build stages on the build host avoids QEMU stalls while BuildKit
# still selects the requested ARM64 Nginx image for the production stage.
FROM --platform=$BUILDPLATFORM ${NODE_IMAGE} AS dependencies
WORKDIR /app
COPY apps/web/package*.json ./
RUN npm ci

FROM dependencies AS build
COPY apps/web ./
ARG VITE_API_BASE_URL=""
ARG VITE_WS_URL=/api/v1/ws/live
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_WS_URL=${VITE_WS_URL}
RUN npm run build

FROM dependencies AS development
COPY apps/web ./

EXPOSE 5173
CMD ["npm", "run", "dev"]

FROM ${NGINX_IMAGE} AS production
COPY infra/nginx.production.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
STOPSIGNAL SIGQUIT
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1/nginx-health >/dev/null || exit 1
