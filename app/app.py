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


app = Flask(__name__)


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


# Middleware
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


# Routes
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
    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
