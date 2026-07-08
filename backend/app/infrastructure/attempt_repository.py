"""In-memory attempt storage.

An exam attempt only needs to outlive the sitting, so a process-local dict is
enough and keeps the app dependency-free. Swap this for a persistent
implementation (same port) if attempts must survive restarts.
"""
from __future__ import annotations

from ..domain.models import Attempt


class InMemoryAttemptRepository:
    def __init__(self) -> None:
        self._store: dict[str, Attempt] = {}

    def save(self, attempt: Attempt) -> None:
        self._store[attempt.id] = attempt

    def get(self, attempt_id: str) -> Attempt | None:
        return self._store.get(attempt_id)
