# Docker Lab — Flask + Docker + CI/CD

A compact **DevOps playground project**: a minimal Flask application packaged in Docker, orchestrated with Compose, and delivered via a **full CI/CD pipeline**. The repository demonstrates **containerization best practices, testing, linting, image scanning, GitHub Actions workflows, multi-container orchestration, and automated deployment**.

---

## 🚀 Project Overview

This repository includes:
- **Flask application** (`app.py`) exposing a `/healthz` endpoint.
- **Two‑stage Dockerfile** (`app/Dockerfile`) — reproducible builds with prebuilt wheels, tiny runtime image, non‑root user, and `tini` init.
- **Unit & integration tests** (Pytest).
- **GitHub Actions CI/CD pipeline** with:
  - Linting (`ruff`, `black`)
  - Unit tests
  - Integration tests with Compose (app + PostgreSQL)
  - Build and vulnerability scan (Trivy)
  - Push to GitHub Container Registry (GHCR)
  - Deployment with Docker Compose
- **docker-compose.yml** — multi‑container orchestration (Flask app + PostgreSQL + persistent volume).
- **Backup script** for PostgreSQL data (example of operations automation).

---

## 🛠️ Tech Stack

- **Language**: Python 3.13
- **Framework**: Flask
- **Database**: PostgreSQL 17
- **Container**: Docker (two‑stage build)
- **Orchestration**: Docker Compose
- **CI/CD**: GitHub Actions → build → test → scan → push → deploy
- **Registry**: GitHub Container Registry (GHCR)
- **Security**: Trivy vulnerability scan

---

## 🔧 Local Development

### Run locally (without Docker)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
pip install -r app/requirements-dev.txt
python -m app
```

### Run with Docker only
```bash
# Build image
docker build -t docker_lab:local ./app

# Run container
docker run --rm -p 8000:8000 --name docker_lab_local docker_lab:local

# Health check
curl -s http://localhost:8000/healthz
```

### Run with Docker Compose (app + db)
```bash
# Start stack
docker compose up --build -d

# App available on http://localhost:8081

# Stop stack
docker compose down
```

Default DB credentials (from compose):
- user: `user`
- password: `pass`
- db: `testdb`
- host: `db` (inside Compose network)

---

## 📦 Dockerfile Highlights

- Multi‑stage build (builder → runtime)
- Prebuilt wheels for reproducibility & speed
- Slim runtime image, no build tools shipped
- Runs as **non‑root** user `app`
- Includes `tini` as PID 1 (better signal handling & process reaping)
- HEALTHCHECK defined for `/healthz`
- OCI labels for metadata

---

## 🔄 CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`):

1. **Test & Lint**
   - Install deps
   - Run unit tests with Pytest
   - Lint with Ruff, format check with Black

2. **Integration Test**
   - Spin up app + Postgres with Compose
   - Wait until `/healthz` is healthy
   - Tear down

3. **Build & Scan**
   - Build Docker image from `app/Dockerfile`
   - Tag as `:latest` and with commit SHA
   - Scan with Trivy (`CRITICAL`/`HIGH` severity)

4. **Push**
   - Log in to GHCR
   - Push both tags to `ghcr.io/nailamber/docker_lab`

5. **Deploy**
   - Log in to GHCR
   - Pull latest image
   - Deploy with `docker compose up -d`

👉 Images are available in **[GHCR Packages](https://github.com/NailAmber?tab=packages)**. Each commit produces a SHA‑tagged image for reproducibility & rollback.

---

## 🛡️ Security Notes

- No secrets in Dockerfile → use environment variables / secret managers.
- Vulnerability scans with Trivy in CI.
- Run containers as **non‑root**.
- `.dockerignore` excludes dev/test files, `.git`, `.venv`, etc.

---

## 💾 Backup Automation

A simple `backup.sh` script is provided:
- Dumps PostgreSQL DB (`pg_dump`)
- Archives with timestamp (`.gz`)
- (Can be run via cron / GitHub Actions job)

---

## 🎤 Demo Tips (Interview Ready)

1. **Elevator pitch:** Pet‑project showing Docker best practices, Compose orchestration, CI/CD pipeline, security scan, and automated deploy.
2. Show Dockerfile → multi‑stage build, non‑root user, `tini`, healthcheck.
3. Show `docker-compose.yml` → multi‑container setup, persistent volume, networking.
4. Show CI/CD pipeline in Actions → explain each stage.
5. Show GHCR package with tags → explain rollback strategy.
6. Run app locally, curl `/healthz`.
7. Mention monitoring/alerting and backups as next steps.

---

## 📚 Next Improvements

- Add Prometheus + Grafana for metrics & monitoring.
- Add Slack/Discord notifications in CI/CD.
- Publish SBOM & sign images (Cosign).
- Extend deployment target: Kubernetes manifests.

---
