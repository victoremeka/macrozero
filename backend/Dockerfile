# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim AS runtime

# Python + pip defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Minimal system deps (CA certs for TLS)
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install uv via pip (CI-friendly)
RUN python -m pip install --no-cache-dir uv

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies into the system environment (no dev deps)
RUN uv sync --frozen --no-dev

# Copy application code
COPY . /app

# Create non-root user
RUN useradd -u 10001 -r -s /usr/sbin/nologin appuser \
 && chown -R appuser:appuser /app
USER appuser

# Default FastAPI port
EXPOSE 8000
ENV PORT=8000

# Optional: basic healthcheck (adjust path as needed)
# HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
#   CMD python -c "import urllib.request as r; r.urlopen('http://127.0.0.1:8000/').read()" || exit 1

# Entrypoint
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
