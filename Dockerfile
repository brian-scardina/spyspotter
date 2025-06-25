# Multi-stage build for PixelTracker
ARG PYTHON_VERSION=3.9
ARG ALPINE_VERSION=3.18

# Build stage
FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION} as builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust

# Set working directory
WORKDIR /build

# Copy requirements first for better caching
COPY requirements-core.txt requirements-test.txt ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip wheel setuptools && \
    pip install --no-cache-dir -r requirements-core.txt

# Production stage
FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION} as production

# Install runtime dependencies
RUN apk add --no-cache \
    curl \
    ca-certificates \
    tzdata \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1000 pixeltracker && \
    adduser -D -u 1000 -G pixeltracker pixeltracker

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=pixeltracker:pixeltracker . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R pixeltracker:pixeltracker /app

# Switch to non-root user
USER pixeltracker

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import pixeltracker; print('OK')" || exit 1

# Expose port (if running as web service)
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Default command
CMD ["python", "pixeltracker.py", "--help"]

# Enterprise stage (includes ML dependencies)
FROM production as enterprise

USER root

# Copy additional requirements for enterprise
COPY requirements-enterprise.txt requirements-ml.txt ./

# Install additional dependencies
RUN apk add --no-cache \
    libgomp \
    lapack \
    && pip install --no-cache-dir -r requirements-enterprise.txt -r requirements-ml.txt \
    && apk del --purge \
    && rm -rf /var/cache/apk/*

USER pixeltracker

# Development stage (includes test dependencies)
FROM enterprise as development

USER root

# Install development tools
RUN apk add --no-cache \
    git \
    bash \
    vim \
    && pip install --no-cache-dir -r requirements-test.txt

USER pixeltracker

# Override command for development
CMD ["python", "-m", "pytest", "--version"]
