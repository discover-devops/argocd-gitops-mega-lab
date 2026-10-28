"""TaskFlow API - a small production-style service for the GitOps Mega Lab.

Endpoints
  GET  /healthz       liveness  (process is up)
  GET  /readyz        readiness (database reachable)
  GET  /api/version   app version + message (changed via Git in the labs)
  GET  /api/tasks     list tasks
  POST /api/tasks     create a task  {"title": "..."}
"""
import os
import socket
import time
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_MESSAGE = os.getenv("APP_MESSAGE", "Hello from TaskFlow")
APP_ENV = os.getenv("APP_ENV", "dev")

DB_DSN = (
    f"host={os.getenv('DB_HOST', 'taskflow-postgres')} "
    f"port={os.getenv('DB_PORT', '5432')} "
    f"dbname={os.getenv('DB_NAME', 'taskflow')} "
    f"user={os.getenv('DB_USER', 'taskflow')} "
    f"password={os.getenv('DB_PASSWORD', '')} "
    "connect_timeout=3"
)

class TaskIn(BaseModel):
    title: str


def get_conn():
    return psycopg.connect(DB_DSN, autocommit=True)


def init_db(retries: int = 30, delay: int = 2) -> None:
    """Create the table, retrying while Postgres starts up."""
    for attempt in range(1, retries + 1):
        try:
            with get_conn() as conn:
                conn.execute(
                    """CREATE TABLE IF NOT EXISTS tasks (
                           id SERIAL PRIMARY KEY,
                           title TEXT NOT NULL,
                           created_at TIMESTAMPTZ DEFAULT now())"""
                )
            print(f"[taskflow] database ready (attempt {attempt})", flush=True)
            return
        except psycopg.OperationalError as exc:
            print(f"[taskflow] waiting for database ({attempt}/{retries}): {exc}", flush=True)
            time.sleep(delay)
    print("[taskflow] database not reachable; /readyz will report not ready", flush=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="TaskFlow API", version=APP_VERSION, lifespan=lifespan)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1")
        return {"status": "ready"}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"database not ready: {exc}")


@app.get("/api/version")
def version():
    return {
        "version": APP_VERSION,
        "message": APP_MESSAGE,
        "environment": APP_ENV,
        "pod": socket.gethostname(),
    }


@app.get("/api/tasks")
def list_tasks():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at FROM tasks ORDER BY id DESC LIMIT 50"
        ).fetchall()
    return [{"id": r[0], "title": r[1], "created_at": r[2].isoformat()} for r in rows]


@app.post("/api/tasks", status_code=201)
def create_task(task: TaskIn):
    title = task.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    with get_conn() as conn:
        row = conn.execute(
            "INSERT INTO tasks (title) VALUES (%s) RETURNING id", (title[:200],)
        ).fetchone()
    return {"id": row[0], "title": title[:200]}
