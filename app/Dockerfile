# ----- Build Stage -----
FROM python:3.13-slim-bookworm AS builder
WORKDIR /app

# Speed up pip
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1

# Update pip, setuptools, wheel first
RUN pip install --upgrade pip setuptools wheel

# Install temp build deps
RUN apt-get update \
	&& apt-get install -y --no-install-recommends build-essential \
	&& rm -rf /var/lib/apt/lists/*

# Copy only requirements.txt first for better caching
COPY requirements.txt .

# Build wheels
RUN pip wheel --wheel-dir /wheels -r requirements.txt


# ----- Runtime Stage -----
FROM python:3.13-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/NailAmber/Docker_lab"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Environment vars for Python and runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_NO_CACHE_DIR=1 \
	APP_ENV=prod \
	PATH="/home/app/.local/bin:$PATH"

# Install tini for better signal handling
RUN apt-get update \
	&& apt-get upgrade \
	&& apt-get install -y --no-install-recommends tini curl \
	&& apt-get purge -y --auto-remove \
	&& rm -rf /var/lib/apt/lists/*

# Create non-root user and app dirs
RUN useradd -m -d /app app \
	&& mkdir -p /tmp/metrics \
	&& chown -R app:app /tmp/metrics

# Copy wheels and requirements
COPY --from=builder /wheels /wheels
COPY requirements.txt .

# Install dependencies from wheels
RUN pip install --no-index --find-links=/wheels --no-cache-dir -r requirements.txt \
	&& rm -rf /wheels

# Copy source code (with correct ownership)
COPY --chown=app:app . . 

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
	CMD curl -fs http://127.0.0.1:8000/health || exit 1

# Use tini as entrypoint, CMD for app 
ENTRYPOINT ["tini", "--"]
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]

