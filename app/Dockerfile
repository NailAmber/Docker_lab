FROM python:3.13-slim AS builder
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt

FROM python:3.13-slim
LABEL org.opencontainers.image.source="https://github.com/NailAmber/Docker_lab"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 APP_ENV=prod

# Optional: install tini for better signal handling (small extra layer)
RUN apt-get update \
  && apt-get install -y --no-install-recommends tini \
  && rm -rf /var/lib/apt/lists/*

RUN useradd -m app \
  && mkdir -p /app && chown -R app:app /app \
  && mkdir -p /tmp/metrics && chown -R app:app /tmp/metrics

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels --no-cache-dir -r requirements.txt && rm -rf /wheels
COPY . .

# Ensure runtime user owns files copied into the image
RUN chown -R app:app /app

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD ["python", "-c", "import sys,urllib.request as u; sys.exit(0) if u.urlopen('http://127.0.0.1:8000/health').status==200 else sys.exit(1)"]

# Use tini to forward signals and reap processes
ENTRYPOINT ["tini", "--", "gunicorn", "-c", "gunicorn.conf.py", "app:app"]
