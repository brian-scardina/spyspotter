# Multi-stage build for PixelTracker with configurable entrypoints
ARG PYTHON_VERSION=3.11
ARG ALPINE_VERSION=3.18
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=latest

# Builder stage - common for all variants
FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION} as builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust \
    make \
    linux-headers

# Set working directory
WORKDIR /build

# Copy requirements files for layer caching
COPY requirements-core.txt requirements-ml.txt requirements-enterprise.txt requirements-test.txt ./

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install wheel
RUN pip install --no-cache-dir --upgrade pip wheel setuptools

# ===========================
# CORE STAGE - Basic functionality
# ===========================
FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION} as core

# Metadata labels
LABEL maintainer="PixelTracker Team" \
      version="${VERSION}" \
      description="PixelTracker Core - Basic tracking pixel detection" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}" \
      stage="core"

# Install runtime dependencies
RUN apk add --no-cache \
    curl \
    ca-certificates \
    tzdata \
    tini \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1000 pixeltracker && \
    adduser -D -u 1000 -G pixeltracker pixeltracker

# Install core dependencies in fresh venv
WORKDIR /build
COPY requirements-core.txt ./
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip wheel setuptools && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements-core.txt

# Set up application directory
WORKDIR /app

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=pixeltracker:pixeltracker . .

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/data /app/config.d /app/cache && \
    chown -R pixeltracker:pixeltracker /app && \
    chmod +x /app/pixeltracker.py

# Copy entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch to non-root user
USER pixeltracker

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app'); import pixeltracker; print('OK')" || exit 1

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIXELTRACKER_STAGE=core \
    PIXELTRACKER_CONFIG_DIR=/app/config.d \
    PIXELTRACKER_DATA_DIR=/app/data \
    PIXELTRACKER_LOG_DIR=/app/logs

# Use tini as init
ENTRYPOINT ["/sbin/tini", "--", "/entrypoint.sh"]
CMD ["pixeltracker.py", "--help"]

# ===========================
# ML STAGE - Machine Learning capabilities
# ===========================
FROM core as ml

# Update metadata
LABEL description="PixelTracker ML - Core + Machine Learning capabilities" \
      stage="ml"

USER root

# Install ML runtime dependencies
RUN apk add --no-cache \
    libstdc++ \
    libgomp \
    lapack \
    libgfortran \
    openblas \
    && rm -rf /var/cache/apk/*

# Install ML dependencies
COPY requirements-ml.txt ./
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements-ml.txt

# Update environment
ENV PIXELTRACKER_STAGE=ml \
    PIXELTRACKER_ML_ENABLED=true

USER pixeltracker

# Updated health check for ML
HEALTHCHECK --interval=30s --timeout=15s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app'); import pixeltracker; import numpy; print('OK')" || exit 1

# ===========================
# ENTERPRISE STAGE - Full enterprise features
# ===========================
FROM ml as enterprise

# Update metadata
LABEL description="PixelTracker Enterprise - Full feature set with ML and enterprise capabilities" \
      stage="enterprise"

USER root

# Install enterprise runtime dependencies
RUN apk add --no-cache \
    redis \
    postgresql-client \
    && rm -rf /var/cache/apk/*

# Install enterprise dependencies
COPY requirements-enterprise.txt ./
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements-enterprise.txt

# Create additional enterprise directories
RUN mkdir -p /app/backups /app/monitoring && \
    chown -R pixeltracker:pixeltracker /app/backups /app/monitoring

# Update environment
ENV PIXELTRACKER_STAGE=enterprise \
    PIXELTRACKER_ENTERPRISE_ENABLED=true \
    PIXELTRACKER_REDIS_ENABLED=true \
    PIXELTRACKER_MONITORING_ENABLED=true

USER pixeltracker

# Enterprise health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=15s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app'); import pixeltracker; import numpy; import redis; print('OK')" || exit 1

# Expose additional ports for enterprise features
EXPOSE 8080 8081 9090

# ===========================
# DEVELOPMENT STAGE - Development tools
# ===========================
FROM enterprise as development

# Update metadata
LABEL description="PixelTracker Development - Full feature set with development tools" \
      stage="development"

USER root

# Install development tools
RUN apk add --no-cache \
    git \
    bash \
    vim \
    nano \
    htop \
    strace \
    && rm -rf /var/cache/apk/*

# Install test and development dependencies
COPY requirements-test.txt ./
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements-test.txt

# Update environment
ENV PIXELTRACKER_STAGE=development \
    PIXELTRACKER_DEBUG=true \
    PIXELTRACKER_LOG_LEVEL=DEBUG

USER pixeltracker

# Override command for development
CMD ["bash"]
