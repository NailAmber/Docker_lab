# Docker_lab

A compact Docker + Python lab: a minimal Flask application packaged with Docker to demonstrate containerization best-practices, reproducible builds, testing, linting and a simple CI image-scan pipeline.

---

## Project summary

This repository contains:
- A small Flask application (app.py) with a health endpoint.
- A two-stage Dockerfile that builds wheels in a builder stage and installs them into a slim runtime image.
- Tests (pytest) and a development requirements file.
- A CI workflow (github_workflows_ci.yml) that runs tests, lint and scans the built image with Trivy.

---

## Quick facts

- Language: Python (3.13 in the Dockerfile)
- Container image: two-stage build (builder -> runtime), wheels pre-built in the builder
- Exposed port: 8000
- CI: GitHub Actions workflow included (github_workflows_ci.yml)

---

## Local quickstart — build and run

1. Build the image
   ```bash
   docker build -t docker_lab:local .
   ```

2. Run container (example uses port 8000)
   ```bash
   docker run --rm -p 8000:8000 --name docker_lab_local docker_lab:local
   ```

3. Verify
   - Open: http://localhost:8000/
   - Health endpoint:
     ```bash
     curl -sS http://localhost:8000/healthz || true
     ```

Notes:
- The runtime image includes `tini` to improve signal handling when running Gunicorn.
- The Dockerfile sets reasonable HEALTHCHECK settings so orchestrators can determine container health.

---

## Development workflow (run locally)

1. Create virtualenv & install
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. Run app locally (dev)
   ```bash
   # run Flask built-in server for development
   python -m app
   ```

3. Run tests
   ```bash
   pytest -q
   ```

4. Lint / format
   ```bash
   ruff check .
   black .
   ```

---

## Dockerfile — summary of important choices

This repository's Dockerfile implements a two-stage build:

Builder stage
- Uses `python:3.13-slim` and installs build-essential to produce wheels.
- Builds wheels with `pip wheel --wheel-dir /wheels -r requirements.txt`. This helps produce deterministic installs and reduces the need for network access in the runtime stage.

Runtime stage
- Also uses `python:3.13-slim` for consistency.
- Adds standard OCI LABELs (source, license).
- Installs `tini` for PID 1 signal forwarding and process reaping.
- Copies prebuilt wheels from the builder and installs them with `--no-index --find-links=/wheels --no-cache-dir`.
- Creates a non-root user `app` and ensures `/app` ownership (there's an explicit `chown -R app:app /app` after copying sources).
- Uses an exec-form ENTRYPOINT that launches `tini` and `gunicorn`:
  ```
  ENTRYPOINT ["tini", "--", "gunicorn", "-c", "gunicorn.conf.py", "app:app"]
  ```
- Includes a conservative HEALTHCHECK against `/healthz` with a longer start-period and timeout to avoid flapping checks during startup.

Why these choices matter
- Two-stage builds keep final images small and avoid shipping build tools.
- Prebuilt wheels improve reproducibility and speed of final installs.
- Running as non-root and using `tini` improves container security and robustness.
- A HEALTHCHECK helps orchestrators (and you) detect non-responsive containers sooner.

---

## Tests, linting & CI

- Tests are written with pytest (see `tests/`).
- Linting is configured with ruff and code formatting with black (dev tools listed in `requirements-dev.txt`).
- A GitHub Actions workflow is included as `github_workflows_ci.yml` which:
  - Installs dependencies
  - Runs tests and lints
  - Builds the Docker image
  - Runs a Trivy scan against the built image

This demonstrates a lightweight CI pipeline that can be extended to publish and sign images.

---

## .dockerignore

To keep build contexts small and avoid leaking local files, the repository includes a `.dockerignore` that excludes:
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

## Security & supply chain notes

- Do not bake secrets into images; use environment variables, secret managers or orchestration-level secrets at runtime.
- Run `trivy` locally or in CI to detect vulnerabilities:
  ```bash
  trivy image docker_lab:local
  ```
- Consider signing released images (cosign) and publishing provenance attestations for production deployment.

---

## Deployment / demo tips

- docker-compose (local):
  ```yaml
  version: "3.8"
  services:
    app:
      build: .
      image: docker_lab:local
      ports:
        - "8000:8000"
      healthcheck:
        test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
        interval: 30s
        timeout: 5s
        retries: 3
  ```

- Kubernetes:
  - Add a Deployment with resource requests/limits, readiness and liveness probes using `/healthz`.
  - Use ConfigMaps and Secrets to inject configuration and secrets.

---

## How to demo this in an interview

1. 30s elevator: goals — containerization, reproducible builds, tests, linting, CI and basic security scanning.
2. Show the Dockerfile and explain the multi-stage build, wheel-building, non-root user, tiny init (`tini`) and the HEALTHCHECK.
3. Build and run the image locally and curl `/healthz`.
4. Run tests locally (`pytest`) and show the CI workflow run in GitHub Actions.
5. Show `trivy` output and explain how you'd gate deployments on scan results.

---
