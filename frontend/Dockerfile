# ---------- Build ----------
FROM node:20-alpine AS build
WORKDIR /app

COPY package.json ./
RUN npm install --no-audit --no-fund

COPY . .
ARG VITE_API_BASE_URL=http://localhost:8002
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build


# ---------- Runtime ----------
FROM nginxinc/nginx-unprivileged:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD wget -q -O- http://localhost:8080/ >/dev/null 2>&1 || exit 1