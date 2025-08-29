# Docker_lab

A compact Docker + Python lab: a minimal Flask application packaged with Docker to demonstrate containerization best-practices, reproducible builds, testing, linting and a simple CI image-scan pipeline. Now includes a `docker-compose.yml` example and a PostgreSQL service for multi-container orchestration.

---

## Project summary

This repository contains:
- A small Flask application (`app.py`) with a health endpoint.
- A two-stage Dockerfile (`app/Dockerfile`) that builds wheels in a builder stage and installs them into a slim runtime image.
- Tests (`pytest`) and development requirements file.
- A CI workflow (`github_workflows_ci.yml`) that runs tests, lint and scans the built image with Trivy.
- **New:** A `docker-compose.yml` for local orchestration with a PostgreSQL database and the app container.

---

## Quick facts

- Language: Python (3.13 in the Dockerfile)
- Container image: two-stage build (builder -> runtime), wheels pre-built in the builder
- Exposed port: 8000 (app), mapped to 8081 in compose
- CI: GitHub Actions workflow included (`github_workflows_ci.yml`)
- **Compose:** Includes a PostgreSQL 17 container and persistent volume

---

## Local quickstart — build and run

### Docker only

1. Build the image
   ```bash
   docker build -t docker_lab:local ./app
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

### Docker Compose (multi-container app + db)

1. Start all services
   ```bash
   docker-compose up --build
   ```

2. App will be available on [http://localhost:8081/](http://localhost:8081/) (forwarded to container port 8000).

3. Database credentials (for development):
   - User: `user`
   - Password: `pass`
   - DB name: `testdb`
   - Hostname (inside compose network): `db`

4. Stop services
   ```bash
   docker-compose down
   ```

Notes:
- The runtime image includes `tini` for improved signal handling when running Gunicorn.
- The Dockerfile sets HEALTHCHECK settings so orchestrators can determine container health.
- Compose sets up a named volume for persistent Postgres data.

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

This repository's Dockerfile (`app/Dockerfile`) implements a two-stage build:

**Builder stage**
- Uses `python:3.13-slim` and installs build-essential to produce wheels.
- Builds wheels with `pip wheel --wheel-dir /wheels -r requirements.txt`. This helps produce deterministic installs and reduces the need for network access in the runtime stage.

**Runtime stage**
- Also uses `python:3.13-slim` for consistency.
- Adds standard OCI LABELs (source, license).
- Installs `tini` for PID 1 signal forwarding and process reaping.
- Copies prebuilt wheels from the builder and installs them with `--no-index --find-links=/wheels --no-cache-dir`.
- Creates a non-root user `app` and ensures `/app` ownership (`chown -R app:app /app` after copying sources).
- Uses an exec-form ENTRYPOINT that launches `tini` and `gunicorn`:
  ```
  ENTRYPOINT ["tini", "--", "gunicorn", "-c", "gunicorn.conf.py", "app:app"]
  ```
- Includes a conservative HEALTHCHECK against `/healthz` with a longer start-period and timeout to avoid flapping checks during startup.

Why these choices matter:
- Two-stage builds keep final images small and avoid shipping build tools.
- Prebuilt wheels improve reproducibility and speed of final installs.
- Running as non-root and using `tini` improves container security and robustness.
- A HEALTHCHECK helps orchestrators (and you) detect non-responsive containers sooner.

---

## Tests, linting & CI

- Tests are written with pytest (`tests/`).
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

- **docker-compose (local):**
  See `docker-compose.yml` for a sample multi-container setup with app and PostgreSQL, persistent volumes, and healthchecks:
  ```yaml
  services:
    db:
      image: postgres:17
      environment:
        POSTGRES_USER: user
        POSTGRES_PASSWORD: pass
        POSTGRES_DB: testdb
      volumes:
        - db_data:/var/lib/postgresql/data
      networks:
        - backend_net
    app:
      build:
        context: ./app
        dockerfile: Dockerfile
      ports:
        - "8081:8000"
      networks:
        - backend_net
  volumes:
    db_data:
  networks:
    backend_net:
  ```

- **Kubernetes:**
  - Add a Deployment with resource requests/limits, readiness and liveness probes using `/healthz`.
  - Use ConfigMaps and Secrets to inject configuration and secrets.
  - For multi-container setup, adapt the compose network to Kubernetes Services.

---

## How to demo this in an interview

1. 30s elevator: goals — containerization, reproducible builds, tests, linting, CI, basic security scanning, and local orchestration with Compose.
2. Show the Dockerfile and explain the multi-stage build, wheel-building, non-root user, tiny init (`tini`), and the HEALTHCHECK.
3. Show `docker-compose.yml` and explain the app+db setup, volumes, and healthchecks.
4. Build and run the image locally and curl `/healthz`.
5. Run tests locally (`pytest`) and show the CI workflow run in GitHub Actions.
6. Show `trivy` output and explain how you'd gate deployments on scan results.

---
