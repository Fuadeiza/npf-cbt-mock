"""The exam configurations offered to candidates.

These are business rules, not user settings, so they live in the domain.
"""
from __future__ import annotations

from .models import ExamMode

EXAM_MODES: tuple[ExamMode, ...] = (
    ExamMode("quick", "Quick Drill", question_count=10, duration_seconds=8 * 60),
    ExamMode("short", "Short Mock", question_count=20, duration_seconds=15 * 60),
    ExamMode("standard", "Standard Mock", question_count=30, duration_seconds=20 * 60),
    ExamMode("full", "Full Mock", question_count=60, duration_seconds=30 * 60),
)

_BY_CODE = {m.code: m for m in EXAM_MODES}


def get_mode(code: str) -> ExamMode | None:
    return _BY_CODE.get(code)
