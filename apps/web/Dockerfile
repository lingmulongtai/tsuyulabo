# syntax=docker/dockerfile:1
FROM node:22-slim AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
RUN --mount=type=cache,target=/root/.npm npm ci

FROM dependencies AS builder
ENV NEXT_TELEMETRY_DISABLED=1
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_DEV_TOOLS=0
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_DEV_TOOLS=$NEXT_PUBLIC_DEV_TOOLS
COPY apps/web/ apps/web/
# Next 16's environment-driven default avoids changing the shared next.config.ts.
# On upgrading Next, verify this flag or use the explicit config line in docs/infra.md.
RUN mkdir -p apps/web/public \
    && NEXT_PRIVATE_STANDALONE=1 npm run build \
    && test -f apps/web/.next/standalone/apps/web/server.js

FROM node:22-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000
COPY --from=builder --chown=node:node /app/apps/web/.next/standalone ./
COPY --from=builder --chown=node:node /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder --chown=node:node /app/apps/web/public ./apps/web/public
USER node
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
