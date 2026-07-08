"""Tests for the exam use cases and domain scoring.

A deterministic RNG and clock keep selection, shuffling, and timing
reproducible.
"""
from __future__ import annotations

import random

import pytest

from app.application.errors import (
    AttemptAlreadySubmitted,
    AttemptNotFound,
    InvalidCandidateName,
    ModeNotFound,
)
from app.application.exam_service import ExamService
from app.domain.models import Choice, Question
from app.infrastructure.attempt_repository import InMemoryAttemptRepository


class FakeQuestionRepo:
    def __init__(self, questions: list[Question]) -> None:
        self._questions = questions

    def all(self) -> list[Question]:
        return list(self._questions)


def make_questions(n: int) -> list[Question]:
    out = []
    for i in range(1, n + 1):
        out.append(
            Question(
                id=i,
                number=i,
                category="Mathematics" if i % 2 else "English",
                text=f"Question {i}: pick B",
                choices=(
                    Choice("A", f"wrong-{i}-a"),
                    Choice("B", f"right-{i}"),
                    Choice("C", f"wrong-{i}-c"),
                    Choice("D", f"wrong-{i}-d"),
                ),
                answer="B",
                confidence="high",
                note="",
                practice=False,
            )
        )
    return out


class Clock:
    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t


@pytest.fixture
def service() -> ExamService:
    return ExamService(
        questions=FakeQuestionRepo(make_questions(60)),
        attempts=InMemoryAttemptRepository(),
        rng=random.Random(42),
        clock=Clock(),
    )


def test_modes_available(service: ExamService) -> None:
    codes = {m.code for m in service.list_modes()}
    assert codes == {"quick", "short", "standard", "full"}


def test_start_attempt_selects_right_count_and_hides_answers(service: ExamService) -> None:
    attempt = service.start_attempt("Ada", "quick")
    assert len(attempt.questions) == 10
    # Presented choices expose only opaque tokens, never the letter key.
    for q in attempt.questions:
        for c in q.choices:
            assert not hasattr(c, "key")
            assert len(c.token) == 32


def test_blank_name_rejected(service: ExamService) -> None:
    with pytest.raises(InvalidCandidateName):
        service.start_attempt("   ", "quick")


def test_unknown_mode_rejected(service: ExamService) -> None:
    with pytest.raises(ModeNotFound):
        service.start_attempt("Ada", "nope")


def _correct_token(attempt, q) -> str:
    return attempt._correct_tokens[q.id]


def test_perfect_score(service: ExamService) -> None:
    attempt = service.start_attempt("Ada", "short")
    answers = {q.id: _correct_token(attempt, q) for q in attempt.questions}
    result = service.submit_attempt(attempt.id, answers)
    assert result.total == 20
    assert result.correct == 20
    assert result.percentage == 100.0
    assert result.unanswered == 0


def test_partial_and_unanswered(service: ExamService) -> None:
    attempt = service.start_attempt("Ada", "quick")
    qs = list(attempt.questions)
    answers = {}
    # 6 correct, 2 wrong, 2 unanswered
    for q in qs[:6]:
        answers[q.id] = _correct_token(attempt, q)
    for q in qs[6:8]:
        wrong = next(c.token for c in q.choices if c.token != _correct_token(attempt, q))
        answers[q.id] = wrong
    result = service.submit_attempt(attempt.id, answers)
    assert result.correct == 6
    assert result.incorrect == 2
    assert result.unanswered == 2
    assert result.percentage == 60.0


def test_resubmission_blocked(service: ExamService) -> None:
    attempt = service.start_attempt("Ada", "quick")
    service.submit_attempt(attempt.id, {})
    with pytest.raises(AttemptAlreadySubmitted):
        service.submit_attempt(attempt.id, {})


def test_unknown_attempt(service: ExamService) -> None:
    with pytest.raises(AttemptNotFound):
        service.submit_attempt("does-not-exist", {})


def test_time_taken_recorded(service: ExamService) -> None:
    clock = Clock()
    svc = ExamService(
        questions=FakeQuestionRepo(make_questions(60)),
        attempts=InMemoryAttemptRepository(),
        rng=random.Random(1),
        clock=clock,
    )
    attempt = svc.start_attempt("Ada", "quick")
    clock.t += 125  # two minutes five seconds later
    result = svc.submit_attempt(attempt.id, {})
    assert result.time_taken_seconds == 125
