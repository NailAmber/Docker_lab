# Docker Lab — Flask + Docker + CI/CD + Monitoring

A compact **DevOps playground project**: a minimal Flask application packaged in Docker, orchestrated with Compose, monitored with Prometheus and Grafana (including alerting), and delivered via a **full CI/CD pipeline**. The repository demonstrates **containerization, automation, observability, and best practices** for modern DevOps workflows.

---

## 🚀 Project Overview

This repository includes:
- **Flask application** (`app.py`) exposing `/` (demo), `/health` (readiness check), and `/metrics` (Prometheus metrics) endpoints.
- **Two‑stage Dockerfile** (`app/Dockerfile`): reproducible builds, prebuilt wheels, tiny runtime image, non‑root user, and `tini` init.
- **Unit & integration tests** (Pytest).
- **GitHub Actions CI/CD pipeline**:
  - Linting (`ruff`, `black`)
  - Unit tests
  - Integration tests with Compose (app + PostgreSQL + Prometheus + Grafana)
  - Backup script verification
  - Build and vulnerability scan (Trivy)
  - Push to GitHub Container Registry (GHCR)
  - Automated deployment with Docker Compose
- **docker-compose.yml**: multi‑container orchestration (Flask app, PostgreSQL, Prometheus, Grafana, node-exporter + persistent volumes).
- **Backup script** for PostgreSQL data (automation example).
- **Grafana dashboard** with panels for QPS, errors, latency, and method breakdown—and built-in alerting for incident response.

---

## 🛠️ Tech Stack

- **Language:** Python 3.13
- **Framework:** Flask
- **Database:** PostgreSQL 17
- **Container:** Docker (multi-stage build)
- **Orchestration:** Docker Compose
- **Monitoring:** Prometheus, Grafana (with alerting), node-exporter
- **CI/CD:** GitHub Actions (build → test → scan → push → deploy)
- **Registry:** GitHub Container Registry (GHCR)
- **Security:** Trivy vulnerability scan

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
curl -s http://localhost:8000/health
```

### Run with Docker Compose (full stack: app, db, monitoring)
```bash
docker compose up --build -d
# App:       http://localhost:8081
# Prometheus: http://localhost:9090
# Grafana:   http://localhost:3000 (default admin/admin)
# Node Exporter: http://localhost:9100
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
- HEALTHCHECK defined for `/health`
- OCI labels for metadata

---

## 🔄 CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci-cd.yml`):

1. **Test & Lint**
   - Install deps
   - Run unit tests with Pytest
   - Lint with Ruff, format check with Black

2. **Integration Test**
   - Bring up full stack (app, Postgres, Prometheus, Grafana, node-exporter) with Compose
   - Wait for `/health` endpoint, and for Prometheus and Grafana to be healthy
   - Verify Prometheus scrapes Flask metrics
   - Verify Grafana sees Prometheus datasource are configured
   - Backup script verification
   - Tear down stack

3. **Build & Scan**
   - Build Docker image from `app/Dockerfile`
   - Tag as `:latest` and with commit SHA
   - Scan with Trivy (`CRITICAL`/`HIGH` severity)

4. **Push**
   - Login to GHCR
   - Push both tags to `ghcr.io/nailamber/docker_lab`

5. **Deploy**
   - Login to GHCR
   - Pull latest image
   - Deploy via Docker Compose

👉 Images are available in **[GHCR Packages](https://github.com/NailAmber?tab=packages)**. Each commit produces a SHA‑tagged image for reproducibility & rollback.

---

## 📊 Monitoring, Metrics & Alerting

- **Prometheus** scrapes Flask `/metrics` for request counts and latency, and node-exporter for host metrics.
- **Grafana** visualizes metrics; includes provisioning for datasources.
- **Alerts** are configured directly in Grafana dashboard panels for errors, latency, or QPS spikes—demonstrating incident response readiness.
- **Healthchecks** for all core services.
- **Integration tests** verify monitoring stack and alerting during CI.

---

## 🛡️ Security Notes

- No secrets in Dockerfile → use environment variables / secret managers.
- Vulnerability scans with Trivy in CI.
- Run containers as **non‑root**.
- `.dockerignore` excludes dev/test files, `.git`, `.venv`, etc.

---

## 💾 Backup Automation

A simple `backup.sh` script:
- Dumps PostgreSQL DB (`pg_dump`)
- Archives with timestamp (`.gz`)
- (Can be run via cron or CI job)
- Backup output is verified in CI pipeline

---

## 🎤 Demo Tips (Interview Ready)

1. **Elevator pitch:** Shows Docker best practices, Compose orchestration, CI/CD pipeline, monitoring/metrics/alerting, security scan, and automated deploy.
2. Demo Dockerfile → multi‑stage build, non‑root user, `tini`, healthcheck.
3. Demo `docker-compose.yml` → orchestrated multi-container setup (app, db, monitoring, volumes).
4. Demo CI/CD pipeline in Actions → explain each stage, especially integration/monitoring and alerting checks.
5. Show GHCR package with tags → explain reproducibility/rollback.
6. Run app locally, curl `/health`.
7. Demo Prometheus & Grafana dashboards, including alert configuration.
8. Highlight backup automation and security.
9. Mention possible next steps.

---

## 📚 Next Improvements

- Add Slack/Discord notifications to CI/CD pipeline or Grafana alerts.
- Publish SBOM & sign images (Cosign).
- Extend deployment target: Kubernetes manifests.
- Add custom alerting rules and incident response playbooks.
- Infrastructure as code (Terraform/Ansible) for cloud deployment.

---
