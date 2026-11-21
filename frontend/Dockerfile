# ── Build stage ──────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json .
RUN npm install

COPY . .
RUN npm run build

# ── Serve stage ───────────────────────────────────────────────────────────────
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx config: proxy /api → backend, serve React for all other routes
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
