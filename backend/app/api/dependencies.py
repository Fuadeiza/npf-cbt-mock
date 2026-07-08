"""Composition root: builds and shares the application services.

A single ExamService (with a single in-memory attempt store) is shared across
requests via a module-level singleton, injected through FastAPI's `Depends`.
"""
from __future__ import annotations

from functools import lru_cache

from ..application.exam_service import ExamService
from ..infrastructure.attempt_repository import InMemoryAttemptRepository
from ..infrastructure.question_repository import JsonQuestionRepository


@lru_cache(maxsize=1)
def get_exam_service() -> ExamService:
    return ExamService(
        questions=JsonQuestionRepository(),
        attempts=InMemoryAttemptRepository(),
    )
