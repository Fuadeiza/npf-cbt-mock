"""The exam use cases: list modes, start an attempt, submit an attempt.

This is the only place the flow is orchestrated. It selects and shuffles
questions, builds the :class:`Attempt` aggregate (keeping the answer key
server-side), and delegates grading back to the aggregate.
"""
from __future__ import annotations

import random
import uuid
from typing import Callable

from ..domain.exam_modes import EXAM_MODES, get_mode
from ..domain.models import (
    Attempt,
    ExamMode,
    PresentedChoice,
    PresentedQuestion,
    Question,
    ScoreResult,
)
from .errors import (
    AttemptAlreadySubmitted,
    AttemptNotFound,
    InvalidCandidateName,
    ModeNotFound,
    NotEnoughQuestions,
)
from .ports import AttemptRepository, QuestionRepository

MAX_NAME_LENGTH = 60


class ExamService:
    def __init__(
        self,
        questions: QuestionRepository,
        attempts: AttemptRepository,
        rng: random.Random | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._questions = questions
        self._attempts = attempts
        self._rng = rng or random.Random()
        self._clock = clock or __import__("time").time

    def list_modes(self) -> tuple[ExamMode, ...]:
        return EXAM_MODES

    def start_attempt(self, candidate_name: str, mode_code: str) -> Attempt:
        name = (candidate_name or "").strip()
        if not name:
            raise InvalidCandidateName("Please enter your name to begin.")
        name = name[:MAX_NAME_LENGTH]

        mode = get_mode(mode_code)
        if mode is None:
            raise ModeNotFound(f"Unknown exam mode: {mode_code!r}")

        pool = self._questions.all()
        if len(pool) < mode.question_count:
            raise NotEnoughQuestions(
                f"Only {len(pool)} questions available, need {mode.question_count}."
            )

        selected = self._rng.sample(pool, mode.question_count)
        attempt = self._build_attempt(name, mode, selected)
        self._attempts.save(attempt)
        return attempt

    def submit_attempt(
        self, attempt_id: str, responses: dict[int, str]
    ) -> ScoreResult:
        attempt = self._attempts.get(attempt_id)
        if attempt is None:
            raise AttemptNotFound("This exam session was not found or has expired.")
        if attempt.submitted:
            raise AttemptAlreadySubmitted("This exam has already been submitted.")

        result = attempt.grade(responses, finished_at=self._clock())
        attempt.submitted = True
        self._attempts.save(attempt)
        return result

    # -- aggregate construction --------------------------------------------

    def _build_attempt(
        self, name: str, mode: ExamMode, selected: list[Question]
    ) -> Attempt:
        presented: list[PresentedQuestion] = []
        correct_tokens: dict[int, str] = {}
        token_text: dict[int, dict[str, str]] = {}
        category: dict[int, str] = {}

        for position, question in enumerate(selected, start=1):
            choices = list(question.choices)
            self._rng.shuffle(choices)

            presented_choices: list[PresentedChoice] = []
            texts: dict[str, str] = {}
            for choice in choices:
                token = uuid.uuid4().hex
                presented_choices.append(PresentedChoice(token=token, text=choice.text))
                texts[token] = choice.text
                if choice.key == question.answer:
                    correct_tokens[question.id] = token

            presented.append(
                PresentedQuestion(
                    id=question.id,
                    number=position,
                    category=question.category,
                    text=question.text,
                    choices=tuple(presented_choices),
                )
            )
            token_text[question.id] = texts
            category[question.id] = question.category

        return Attempt(
            id=uuid.uuid4().hex,
            candidate_name=name,
            mode=mode,
            started_at=self._clock(),
            questions=tuple(presented),
            _correct_tokens=correct_tokens,
            _token_text=token_text,
            _category=category,
        )
