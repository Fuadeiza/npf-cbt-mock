"""FastAPI application factory.

Serves the JSON API under /api and the static frontend at the root, so the
whole app runs from a single process during development.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api.routes import router

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


def create_app() -> FastAPI:
    app = FastAPI(title="NPF CBT Mock Exam", version="1.0.0")

    # Permit a separately-served frontend during development.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    if FRONTEND_DIR.is_dir():
        app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

    return app


app = create_app()
