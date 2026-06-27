# Zweiplus Onboarding frontend — Vite 7 + React 19 (toolchain pinned).
# Stage 1: build the static bundle. VITE_API_URL is a build-time env baked into
# the JS, so it must be provided as a build arg.
FROM node:22-alpine AS build

WORKDIR /app

# Install dependencies from the lockfile (reproducible, pinned).
COPY package.json package-lock.json ./
RUN npm ci

# Build with the backend URL baked in.
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

COPY . .
RUN npm run build

# Stage 2: serve the static dist/ with nginx (SPA fallback to index.html).
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
