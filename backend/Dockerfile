# Multi-stage build for Lux Data Observability Platform Backend
# Stage 1: Build virtual environment and dependencies
FROM python:3.13-slim AS builder

WORKDIR /build

# Install build dependencies for compiling any C-extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create isolated virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy package definitions
COPY backend/pyproject.toml backend/README.md ./
COPY backend/app ./app

# Install dependencies into virtualenv
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Stage 2: Production runtime image
FROM python:3.13-slim AS runtime

WORKDIR /app

# Create non-root system user and group
RUN groupadd -g 1000 lux && \
    useradd -u 1000 -g lux -m -s /bin/bash lux

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Configure runtime environment
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LUX_ENV=production \
    LUX_DATA_DIR=/app/data

# Copy backend application source
COPY backend/app /app/app

# Seed bundled scenarios into data directory
COPY data/scenarios /app/data/scenarios

# Create runtime directories with correct permissions for the non-root user
RUN mkdir -p /app/data/uploads /app/data/artifacts && \
    chown -R lux:lux /app

# Switch to non-root user
USER lux

# Expose backend REST API port
EXPOSE 8000

# Container healthcheck testing /health endpoint
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Start Uvicorn ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

