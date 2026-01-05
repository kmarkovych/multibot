# Build stage
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies (including WeasyPrint requirements)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# Runtime stage
FROM python:3.11-slim-bookworm AS runtime

# Install runtime dependencies for WeasyPrint PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi8 \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r multibot && useradd -r -g multibot multibot

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY config/base.yaml ./config/

# Create directories for mounted configs and custom plugins
RUN mkdir -p /app/config/bots /app/src/plugins/custom /app/logs \
    && chown -R multibot:multibot /app

# Switch to non-root user
USER multibot

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health/live')" || exit 1

# Expose ports
EXPOSE 8080 8443

# Environment defaults
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    HEALTH_CHECK_PORT=8080 \
    ENABLE_HOT_RELOAD=true \
    CONFIG_DIR=/app/config/bots \
    PLUGINS_DIR=/app/src/plugins/custom

# Entry point
CMD ["python", "-m", "src.main"]
