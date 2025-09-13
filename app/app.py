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
import logging
import sys

app = Flask(__name__)

# load .env from repo root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# Get db link and create db engine
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_SERVICE = os.getenv("POSTGRES_SERVICE")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVICE}:5432/{POSTGRES_DB}"

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("app")

if POSTGRES_PASSWORD:
    logDataBaseURL = DATABASE_URL.replace(POSTGRES_PASSWORD, "***")
else:
    logDataBaseURL = DATABASE_URL
logger.info("Using DATABASE_URL=%s", logDataBaseURL)


# Create table if not exists
def init_db(retry_seconds=2, max_retries=10):
    tries = 0
    global engine
    while True:
        try:
            engine = create_engine(DATABASE_URL)
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
            logger.info("Database initialized")
            break
        except Exception as e:
            tries += 1
            logger.warning("DB init failed (try %d/%d): %s", tries, max_retries, e)
            if tries >= max_retries:
                logger.exception("Max retries reached, giving up on DB init")
                raise
            time.sleep(retry_seconds)


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
    latency = time.time() - getattr(request, "start_time", time.time())
    endpoint = request.endpoint or "unknown"
    worker_id = os.environ.get("WORKER_ID", "unknown")
    status_str = str(response.status_code)

    try:
        http_requests_total.labels(
            worker_id=worker_id,
            method=request.method,
            endpoint=endpoint,
            status=status_str,
        ).inc()

        http_requests_latency.labels(
            worker_id=worker_id, method=request.method, endpoint=endpoint
        ).observe(latency)
    except Exception as e:
        logger.exception("Failed to record metrics: %s", e)

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
        return {"status": "error", "detail": "No content"}, 400

    try:
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO messages (content) VALUES (:content)"),
                {"content": content},
            )
        return {"status": "message saved successfully"}
    except Exception as e:
        logger.exception("Failed to add message: %s", e)
        return {"status": "error", "detail": "Could not to save message"}, 500


@app.route("/delete", methods=["POST"])
def del_message():
    data = request.json
    content = data.get("content")
    if not content:
        return {"status": "error", "detail": "No content"}, 400

    try:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM messages WHERE content = (:content)"),
                {"content": content},
            )
        return {"status": "ok", "detail": "message deleted successfully"}
    except Exception as e:
        logger.exception("Failed to delete message: %s", e)
        return {"status": "error", "detail": "Could not to delete message"}, 500


@app.route("/list", methods=["GET"])
def list_messages():
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT id, content FROM messages")).fetchall()
        return jsonify([{"id": row.id, "content": row.content} for row in rows])
    except Exception as e:
        logger.exception("Failed to get list of messages: %s", e)
        return {"status": "error", "detail": "Could not to get list of messages"}, 500


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000)
else:
    try:
        init_db()
    except Exception as e:
        logger.warning("Can't connect to database at startup: %s", e)
