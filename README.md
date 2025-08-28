# Docker_lab

[![Repo Size](https://img.shields.io/github/repo-size/NailAmber/Docker_lab)](https://github.com/NailAmber/Docker_lab)
[![Language](https://img.shields.io/badge/lang-Python%20%2B%20Docker-blue)]()

A compact, well-documented Docker + Python lab: a minimal Python application packaged with Docker to demonstrate containerization best-practices, reproducible builds, testing, and a clean developer workflow.

---

## Project summary

This repository contains:
- A small Python application (service or script).
- A Dockerfile to build a reproducible image.
- Tests (pytest-compatible) and a simple dev workflow.

---

## Quick facts

- Language: Python (3.13 in the Dockerfile)
- Container image: built with a two-stage image that builds wheels then installs them into a slim runtime
- Recommended ports: 8000 (common default)

---

## Local quickstart — build and run

1. Build the image
   ```bash
   docker build -t docker_lab:local .
   ```

2. Run container (example uses port 8000)
   ```bash
   docker run --rm -p 8000:8000 --name docker_lab_local nailamber/docker_lab:local
   ```

3. Verify
   - Open: http://localhost:8000/ (change port/path if your app differs)
   - Or:
     ```bash
     docker logs -f docker_lab_local
     curl -sS http://localhost:8000/healthz || true
     ```

---

## Development workflow

Run locally (without Docker)
1. Create virtualenv & install
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Run app (example)
   ```bash
   python -m app        # or `python app/main.py` — use the repository's entrypoint
   ```

---

## Dockerfile — explanation

This repository's Dockerfile implements a two-stage build (builder -> runtime) using python:3.13-slim. Below I explain what each part does, why it's there, and practical recommendations tied to the exact Dockerfile you have.

1) Base and builder stage
- FROM python:3.13-slim AS builder
  - Uses the slim image for a smaller build environment. Pinning to a specific Python minor (3.13) is good for reproducibility.
- ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
  - Disables pip cache and version check to reduce image size and noisy output during build.
- apt-get install build-essential
  - Installs build tools required to compile wheels for packages with native extensions. These are installed only in the builder stage which keeps the final runtime image smaller.
- COPY requirements.txt .
- RUN pip wheel --wheel-dir /wheels -r requirements.txt
  - Builds wheels for all dependencies and stores them in /wheels. Advantages:
    - Deterministic installs in the final stage (no network needed if wheels are present).
    - Faster installs in the runtime stage because pip can use pre-built wheels.
  - Caveat:
    - Wheels produced here must be compatible with the target runtime platform. If you build on a different platform (e.g., macOS) or for multiple architectures, use docker buildx or a manylinux builder to produce correct wheels.

2) Runtime stage
- FROM python:3.13-slim
  - Keeps runtime base small and consistent with the builder.
- WORKDIR /app
- ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_ENV=prod
  - Good defaults: avoids .pyc files and ensures logs are not buffered.
- RUN useradd -m app && mkdir -p /app && chown -R app:app /app
  - Creates a non-root user `app` and ensures /app ownership. Running as non-root improves container security.
  - Note: Because files are copied later, make sure ownership remains correct for any files added after this command (either copy as root and chown, or chown during copy).
- COPY --from=builder /wheels /wheels
  - Brings pre-built wheels into the runtime image so we can install offline.
- COPY requirements.txt .
- RUN pip install --no-index --find-links=/wheels -r requirements.txt && rm -rf /wheels
  - Installs dependencies from the local wheel cache with --no-index to avoid hitting PyPI, then removes wheels to save space.
  - Suggestion: add --no-cache-dir to pip installs here as well for cleanliness, though PIP_NO_CACHE_DIR is already set in builder; you might set it in this stage too.
- COPY . .
  - Copies application code into /app. For better cache utilization, consider copying only what's needed, or copying requirements first (already done) and then source to maximize layer reuse.
- USER app
  - Drops privileges to run the process as non-root. Confirm files required at runtime are readable/executable by `app`.
- EXPOSE 8000
  - Documents the port the app serves on.
- HEALTHCHECK
  - The Dockerfile uses a Python one-liner to check the /healthz endpoint:
    HEALTHCHECK --interval=10s --timeout=2s --retries=3 --start-period=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz').read()" || exit 1
  - This validates the app is responding. Notes and improvements:
    - The current timeout (2s) is aggressive; increase it (e.g., --timeout=5s) if startup can be slow.
    - Because the HEALTHCHECK runs as the image's default user, ensure python and urllib are available and the user has permission to perform the request.
    - Using curl (if available) or a tiny script included in the image can make the check clearer; alternatively use the exec-form JSON array to avoid shell parsing quirks.
    - Example safer form:
      HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 CMD curl -f http://127.0.0.1:8000/healthz || exit 1
    - If you keep the Python check, prefer:
      HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 CMD ["python", "-c", "import sys,urllib.request; sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:8000/healthz').status==200 else sys.exit(1)"]
- ENTRYPOINT ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
  - Using exec-form ENTRYPOINT is correct: it preserves signals and PID 1 behavior for Gunicorn. Gunicorn handles graceful shutdowns itself.
  - Consider running the container with an init process (tini). Two options:
    - Add tini in the image and set ENTRYPOINT to ["tini", "--", "gunicorn", ...]
    - Or instruct users to run docker with --init (docker run --init ...) to ensure proper reaping of child processes and signal forwarding.
  - Keep gunicorn configuration in gunicorn.conf.py so you can control workers, timeouts, and logging.

3) Practical recommendations & polish items
- LABELs: add standard OCI labels for source, authorship and version:
  ```dockerfile
  LABEL org.opencontainers.image.source="https://github.com/NailAmber/Docker_lab"
  LABEL org.opencontainers.image.licenses="MIT"
  ```
- .dockerignore: ensure you exclude .venv, tests, docs, .git to keep context small (see recommended .dockerignore below).
- Buildx/multi-arch: if you plan to publish multi-arch images, build wheels in a manylinux container or use docker buildx to produce compatible artifacts.
- Ownership and permissions: because you create `app` user before copying, verify that files copied into the image are owned/readable by `app`. If necessary, chown the files after copying, or create and use a builder that sets permissions as part of the copy step.
- Security: prefer minimal base images and strip apt caches in the builder (already done). If you add runtime packages, remove apt lists after install.
- Reproducibility: pin dependency versions in requirements.txt and optionally include a lock file or report the exact pip/pip-tools output used to build wheels.

4) Example small improvements applied to this Dockerfile (suggested minimal patch)
```dockerfile
# after copying sources, ensure app owns files (if copy performed as root)
RUN chown -R app:app /app

# a slightly more conservative healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD ["python", "-c", "import sys,urllib.request; sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:8000/healthz').status==200 else sys.exit(1)"]
```

---

## .dockerignore (recommended)

Include a `.dockerignore` at repo root to keep the image context small and avoid leaking secrets:

```
__pycache__
*.pyc
.env
.venv
.git
.gitignore
tests/
docs/
*.sqlite3
```

---

## CI / GitHub Actions (recommended)

Add a lightweight workflow to build, test, and scan:

- Build and run tests on push/PR
- Build image and run Trivy scan on protected branch
- Push to registry only from main with signed tags (cosign)

Example pipeline steps:
1. checkout
2. setup-python
3. pip install -r requirements-dev.txt
4. pytest
5. docker build (cache + metadata)
6. trivy image scan
7. push

---

## Testing & quality gates

- Unit tests: run on every push (fast)
- Integration/E2E: run in CI on staging environment or in container with dependencies mocked
- Linting: flake8/ruff + black formatting as pre-commit hooks
- Security scanning: trivy, bandit
- Dependency checks: pip-audit or `safety`

Add pre-commit config and ensure tests + linters are required before merge.

---

## Image security & scanning

- Run `trivy image nailamber/docker_lab:local` locally or in CI.
- Sign images with cosign and use Notation/OCI attestations for provenance.
- Use minimal base images and remove package manager caches after install.
- Avoid baking secrets into image — mount secrets at runtime or use secret managers.

---

## Deployment notes

docker-compose (local multi-service)
```yaml
version: "3.8"
services:
  app:
    image: nailamber/docker_lab:local
    build: .
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - ENV=dev
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 3s
      retries: 3
```

Kubernetes (simple manifest):
- Provide Deployment with resource requests/limits, liveness/readiness probes, and PodDisruptionBudget.
- Use ConfigMaps/Secrets for config and environment settings.

---

## How to demo this in an interview

1. 30s elevator: describe goals (containerization, reproducible builds, tests, security).
2. Show the Dockerfile and explain why it's multi-stage, non-root, and cache-friendly.
3. Build the image locally and run it (show logs, curl a health endpoint).
4. Run tests and show CI status (or run the local GitHub Actions runner snippet).
5. Show a quick `trivy` scan and explain how you'd gate deployments on scan results.

Keep it to a 5–7 minute demo: code -> build -> run -> test -> scan.
