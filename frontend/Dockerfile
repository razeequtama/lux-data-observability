# Multi-stage build for Lux Data Observability Platform Frontend
# Stage 1: Build production static bundle
FROM node:22-alpine AS builder

WORKDIR /app

# Copy dependency specifications
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies strictly according to package lock
RUN npm ci

# Copy frontend source code
COPY frontend/ ./

# Compile production bundle
RUN npm run build

# Stage 2: Serve with lightweight Nginx web server
FROM nginx:alpine AS runtime

# Remove default configurations and assets
RUN rm -rf /etc/nginx/conf.d/* /usr/share/nginx/html/*

# Copy custom Nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy production assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose web server port
EXPOSE 3000

# Container healthcheck testing frontend HTTP response
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1:3000/ || exit 1

# Start Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]

