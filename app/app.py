from flask import Flask, jsonify, Response, request
from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
)
from prometheus_client import multiprocess
import os
import time
import random
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# Get db link and create db engine
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_SERVICE = os.getenv("POSTGRES_SERVICE")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVICE}:5432/{POSTGRES_DB}"
print(DATABASE_URL)

engine = create_engine(DATABASE_URL, echo=True, future=True)


# Create table if not exists
def init_db():
    with engine.begin() as conn:
        conn.execute(
            text(
                """
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL

        )
        """
            )
        )


# Create registry for multiprocess
def create_registry():
    if "prometheus_multiproc_dir" in os.environ:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        return registry
    return CollectorRegistry()


# Metrics
http_requests_total = Counter(
    "flask_app_http_requests_total",
    "Total number of HTTP requests received",
    ["worker_id", "method", "endpoint", "status"],
)
http_requests_latency = Histogram(
    "flask_app_http_requests_latency_seconds",
    "Request latency",
    ["worker_id", "method", "endpoint"],
    buckets=[0.05, 0.1, 0.3, 0.5, 0.7, 1, 2, 5],
)


# ----- Middleware -----

@app.before_request
def start_time():
    request.start_time = time.time()


@app.after_request
def record_metrics(response):
    latency = time.time() - request.start_time
    endpoint = request.endpoint or "unknown"
    worker_id = os.environ.get("WORKER_ID", "unknown")

    http_requests_total.labels(
        worker_id=worker_id,
        method=request.method,
        endpoint=endpoint,
        status=response.status_code,
    ).inc()

    http_requests_latency.labels(
        worker_id=worker_id, method=request.method, endpoint=endpoint
    ).observe(latency)

    return response


# ----- Routes -----

@app.route("/", methods=["GET"])
def index():
    # Work emulation
    time.sleep(random.random())

    return jsonify(
        status="ok",
        message="Hello from Flask in Docker with Gunicorn!",
        env=os.getenv("APP_ENV", "dev"),
    )


@app.route("/metrics", methods=["GET"])
def metrics():
    registry = create_registry()
    data = generate_latest(registry)
    return Response(data, mimetype=CONTENT_TYPE_LATEST)


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200


# DB related routes

@app.route("/add", methods=["POST"])
def add_message():
    data = request.json
    content = data.get("content")
    if not content:
        return {"error": "No content"}, 400

    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO messages (content) VALUES (:content)"),
            {"content": content},
        )

    return {"status": "message saved successfully"}


@app.route("/delete", methods=["POST"])
def del_message():
    data = request.json
    content = data.get("content")
    if not content:
        return {"error": "No content"}, 400

    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM messages WHERE content = (:content)"),
            {"content": content},
        )

    return {"status": "message deleted successfully"}


@app.route("/list", methods=["GET"])
def list_messages():
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT id, content FROM messages")).fetchall()
        return jsonify(
            [{"id": row.id, "content": row.content} for row in rows]
        )
    except:
        return {"status": "no list"}


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000)
else:
    init_db()
