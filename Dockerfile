# Multi-Stage Hardened Production Dockerfile for Stubble2Power
# Stage 1: Build stage with compilation tools and wheel caching
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies into a wheel cache directory
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# Stage 2: Minimal runtime image running as unprivileged user
FROM python:3.11-slim AS runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/usr/local/bin:$PATH"

WORKDIR /app

# Install minimal runtime shared libraries only (libpq5 for PostgreSQL, curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python dependencies from builder
COPY --from=builder /install /usr/local

# Create unprivileged system user and group (UID/GID 10001)
RUN groupadd -g 10001 stubble_app && \
    useradd -u 10001 -g stubble_app -s /sbin/nologin -d /app stubble_app && \
    mkdir -p /app/data /app/logs && \
    chown -R stubble_app:stubble_app /app

# Copy application source code with unprivileged ownership
COPY --chown=stubble_app:stubble_app . /app

# Switch to non-root execution
USER stubble_app

EXPOSE 8000 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || curl -f http://localhost:8000/api/v1/health || curl -f http://localhost:8000/ || curl -f http://localhost:8501/_stcore/health || exit 1

# Default command launches FastAPI backend
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
