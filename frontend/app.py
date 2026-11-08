import json
import logging
import os
import time

import requests
from flask import Flask, Response, g, render_template, request
from prometheus_client import (CONTENT_TYPE_LATEST, Counter, Histogram,
                               generate_latest)

app = Flask(__name__)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {"ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
                   "level": record.levelname, "msg": record.getMessage(),
                   "service": "frontend"}
        for key in ("method", "path", "status", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
log = logging.getLogger("frontend")
log.setLevel(os.getenv("LOG_LEVEL", "INFO"))
log.addHandler(handler)
log.propagate = False

REQUESTS = Counter("http_requests_total", "Total HTTP requests",
                   ["service", "method", "endpoint", "status"])
LATENCY = Histogram("http_request_duration_seconds", "Request latency",
                    ["service", "method", "endpoint"])
UPSTREAM_ERRORS = Counter("backend_upstream_errors_total",
                          "Failed calls from frontend to backend")


@app.before_request
def start_timer():
    g.start = time.perf_counter()


@app.after_request
def record(resp):
    if request.path == "/metrics":
        return resp
    elapsed = time.perf_counter() - g.start
    endpoint = request.url_rule.rule if request.url_rule else "unmatched"
    REQUESTS.labels("frontend", request.method, endpoint, resp.status_code).inc()
    LATENCY.labels("frontend", request.method, endpoint).observe(elapsed)
    log.info("request", extra={"method": request.method, "path": request.path,
                               "status": resp.status_code,
                               "duration_ms": round(elapsed * 1000, 1)})
    return resp


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route("/api/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy(path):
    """Browser -> frontend -> backend. Backend is never exposed publicly."""
    try:
        r = requests.request(
            request.method, f"{BACKEND_URL}/api/{path}",
            json=request.get_json(silent=True), timeout=5)
        return Response(r.content, status=r.status_code,
                        content_type=r.headers.get("Content-Type"))
    except requests.RequestException as e:
        UPSTREAM_ERRORS.inc()
        log.error(f"backend unreachable: {e}")
        return {"error": "backend unavailable"}, 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("FRONTEND_PORT", "8080")))
