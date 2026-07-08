"""Ports (interfaces) the application depends on.

Infrastructure provides the concrete implementations. Depending on these
Protocols keeps the application layer ignorant of storage and file formats.
"""
from __future__ import annotations

from typing import Protocol

from ..domain.models import Attempt, Question


class QuestionRepository(Protocol):
    def all(self) -> list[Question]:
        """Return every question in the bank."""
        ...


class AttemptRepository(Protocol):
    def save(self, attempt: Attempt) -> None: ...

    def get(self, attempt_id: str) -> Attempt | None: ...
