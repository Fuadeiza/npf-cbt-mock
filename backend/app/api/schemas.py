"""Pydantic schemas: the wire format of the HTTP API.

These translate domain objects to/from JSON. Note that response schemas for
starting an attempt deliberately omit the correct answer.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from ..domain.models import Attempt, ExamMode, PresentedQuestion, ScoreResult


class ModeOut(BaseModel):
    code: str
    label: str
    question_count: int
    duration_seconds: int

    @classmethod
    def of(cls, mode: ExamMode) -> "ModeOut":
        return cls(
            code=mode.code,
            label=mode.label,
            question_count=mode.question_count,
            duration_seconds=mode.duration_seconds,
        )


class ChoiceOut(BaseModel):
    token: str
    text: str


class QuestionOut(BaseModel):
    id: int
    number: int
    category: str
    text: str
    choices: list[ChoiceOut]

    @classmethod
    def of(cls, q: PresentedQuestion) -> "QuestionOut":
        return cls(
            id=q.id,
            number=q.number,
            category=q.category,
            text=q.text,
            choices=[ChoiceOut(token=c.token, text=c.text) for c in q.choices],
        )


class StartRequest(BaseModel):
    candidate_name: str = Field(..., min_length=1)
    mode: str


class StartResponse(BaseModel):
    attempt_id: str
    candidate_name: str
    mode: ModeOut
    duration_seconds: int
    questions: list[QuestionOut]

    @classmethod
    def of(cls, attempt: Attempt) -> "StartResponse":
        return cls(
            attempt_id=attempt.id,
            candidate_name=attempt.candidate_name,
            mode=ModeOut.of(attempt.mode),
            duration_seconds=attempt.mode.duration_seconds,
            questions=[QuestionOut.of(q) for q in attempt.questions],
        )


class SubmitRequest(BaseModel):
    # question id -> chosen choice token
    answers: dict[int, str] = Field(default_factory=dict)


class CategoryScoreOut(BaseModel):
    category: str
    correct: int
    total: int


class QuestionReviewOut(BaseModel):
    number: int
    category: str
    text: str
    chosen_text: str | None
    correct_text: str
    is_correct: bool
    answered: bool


class ScoreResponse(BaseModel):
    candidate_name: str
    mode: ModeOut
    total: int
    correct: int
    incorrect: int
    unanswered: int
    percentage: float
    time_taken_seconds: int
    categories: list[CategoryScoreOut]
    review: list[QuestionReviewOut]

    @classmethod
    def of(cls, r: ScoreResult) -> "ScoreResponse":
        return cls(
            candidate_name=r.candidate_name,
            mode=ModeOut.of(r.mode),
            total=r.total,
            correct=r.correct,
            incorrect=r.incorrect,
            unanswered=r.unanswered,
            percentage=r.percentage,
            time_taken_seconds=r.time_taken_seconds,
            categories=[
                CategoryScoreOut(category=c.category, correct=c.correct, total=c.total)
                for c in r.categories
            ],
            review=[
                QuestionReviewOut(
                    number=q.number,
                    category=q.category,
                    text=q.text,
                    chosen_text=q.chosen_text,
                    correct_text=q.correct_text,
                    is_correct=q.is_correct,
                    answered=q.answered,
                )
                for q in r.results
            ],
        )
