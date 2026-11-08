import json
import logging
import os
import random
import time

from flask import Flask, Response, g, jsonify, request
from prometheus_client import (CONTENT_TYPE_LATEST, Counter, Gauge, Histogram,
                               generate_latest)
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# ---------- logging (JSON, one line per event) ----------
class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "msg": record.getMessage(),
            "service": "backend",
        }
        for key in ("method", "path", "status", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
log = logging.getLogger("backend")
log.setLevel(os.getenv("LOG_LEVEL", "INFO"))
log.addHandler(handler)
log.propagate = False

# ---------- metrics ----------
REQUESTS = Counter("http_requests_total", "Total HTTP requests",
                   ["service", "method", "endpoint", "status"])
LATENCY = Histogram("http_request_duration_seconds", "Request latency",
                    ["service", "method", "endpoint"],
                    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5))
DB_ERRORS = Counter("db_errors_total", "Database errors")
TASKS_TOTAL = Gauge("tasks_total", "Tasks by state", ["state"])

# ---------- database ----------
_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = pool.SimpleConnectionPool(
            1, 10,
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "taskboard"),
            user=os.getenv("DB_USER", "taskboard"),
            password=os.getenv("DB_PASSWORD", "changeme"),
            connect_timeout=3,
        )
        conn = _pool.getconn()
        try:
            with conn, conn.cursor() as cur:
                cur.execute("""CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY, title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
        finally:
            _pool.putconn(conn)
    return _pool


def query(sql, params=None, fetch=True):
    p = get_pool()
    conn = p.getconn()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall() if fetch else None
    except Exception:
        DB_ERRORS.inc()
        raise
    finally:
        p.putconn(conn)


def refresh_task_gauge():
    rows = query("SELECT done, COUNT(*) AS n FROM tasks GROUP BY done")
    counts = {r["done"]: r["n"] for r in rows}
    TASKS_TOTAL.labels("done").set(counts.get(True, 0))
    TASKS_TOTAL.labels("open").set(counts.get(False, 0))


# ---------- request hooks ----------
@app.before_request
def start_timer():
    g.start = time.perf_counter()


@app.after_request
def record(resp):
    if request.path == "/metrics":
        return resp
    elapsed = time.perf_counter() - g.start
    endpoint = request.url_rule.rule if request.url_rule else "unmatched"
    REQUESTS.labels("backend", request.method, endpoint, resp.status_code).inc()
    LATENCY.labels("backend", request.method, endpoint).observe(elapsed)
    log.info("request", extra={"method": request.method, "path": request.path,
                               "status": resp.status_code,
                               "duration_ms": round(elapsed * 1000, 1)})
    return resp


# ---------- ops endpoints ----------
@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/ready")
def ready():
    try:
        query("SELECT 1")
        return jsonify(status="ready")
    except Exception as e:
        log.error(f"readiness failed: {e}")
        return jsonify(status="not ready"), 503


@app.get("/metrics")
def metrics():
    try:
        refresh_task_gauge()
    except Exception:
        pass
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


# ---------- API ----------
@app.get("/api/tasks")
def list_tasks():
    rows = query("SELECT id, title, done, created_at FROM tasks ORDER BY id DESC")
    return jsonify(rows)


@app.post("/api/tasks")
def create_task():
    title = (request.get_json(silent=True) or {}).get("title", "").strip()
    if not title:
        return jsonify(error="title is required"), 400
    row = query("INSERT INTO tasks (title) VALUES (%s) RETURNING id, title, done, created_at",
                (title,))[0]
    return jsonify(row), 201


@app.put("/api/tasks/<int:task_id>/toggle")
def toggle_task(task_id):
    rows = query("UPDATE tasks SET done = NOT done WHERE id = %s "
                 "RETURNING id, title, done, created_at", (task_id,))
    if not rows:
        return jsonify(error="not found"), 404
    return jsonify(rows[0])


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    query("DELETE FROM tasks WHERE id = %s", (task_id,), fetch=False)
    return "", 204


# ---------- chaos endpoints (for testing alerts) ----------
@app.get("/api/chaos/error")
def chaos_error():
    """Returns 500 ~50% of the time. Hit in a loop to trigger error-rate alerts."""
    if random.random() < 0.5:
        return jsonify(error="simulated failure"), 500
    return jsonify(status="lucky")


@app.get("/api/chaos/slow")
def chaos_slow():
    """Sleeps 1-3s. Use to trigger latency alerts."""
    time.sleep(random.uniform(1, 3))
    return jsonify(status="slow but ok")


@app.errorhandler(Exception)
def unhandled(e):
    log.error(f"unhandled: {e}")
    return jsonify(error="internal server error"), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("BACKEND_PORT", "5000")))
