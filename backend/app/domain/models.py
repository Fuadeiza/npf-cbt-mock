"""Domain model for the NPF CBT mock exam.

This layer is pure Python: no framework, no I/O. It expresses the business
concepts (questions, exam modes, attempts, scoring) and the rules that govern
them. Everything an outer layer needs to know lives here.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# --- Source material -------------------------------------------------------


@dataclass(frozen=True)
class Choice:
    """One lettered option (A-D) of a question, as authored."""

    key: str
    text: str


@dataclass(frozen=True)
class Question:
    """A question exactly as stored in the bank, including its answer key."""

    id: int
    number: int
    category: str
    text: str
    choices: tuple[Choice, ...]
    answer: str  # the key ("A".."D") of the correct choice
    confidence: str  # "high" | "low"
    note: str
    practice: bool

    def correct_choice(self) -> Choice:
        return next(c for c in self.choices if c.key == self.answer)


@dataclass(frozen=True)
class ExamMode:
    """A selectable exam configuration (business rule, not user input)."""

    code: str
    label: str
    question_count: int
    duration_seconds: int


# --- What the candidate actually sees --------------------------------------
# Choices are shuffled and given opaque tokens so the correct answer never
# leaves the server. The candidate answers with tokens, not letters.


@dataclass(frozen=True)
class PresentedChoice:
    token: str
    text: str


@dataclass(frozen=True)
class PresentedQuestion:
    id: int
    number: int  # display position within this attempt (1-based)
    category: str
    text: str
    choices: tuple[PresentedChoice, ...]


# --- The attempt aggregate --------------------------------------------------


@dataclass
class Attempt:
    """A single candidate sitting a single exam.

    Holds the presented questions and the private token->correctness mapping
    used to grade a submission. This is the consistency boundary: grading a
    set of responses is a method on the aggregate.
    """

    id: str
    candidate_name: str
    mode: ExamMode
    started_at: float  # epoch seconds
    questions: tuple[PresentedQuestion, ...]
    # question id -> the token of its correct choice
    _correct_tokens: dict[int, str] = field(repr=False)
    # question id -> {token: choice text}, for building the review
    _token_text: dict[int, dict[str, str]] = field(repr=False)
    # question id -> source category, for the per-category breakdown
    _category: dict[int, str] = field(repr=False)
    submitted: bool = False

    def grade(self, responses: dict[int, str], finished_at: float) -> "ScoreResult":
        """Score a mapping of {question_id: chosen_token}.

        Unknown question ids and tokens are ignored; missing answers count as
        unanswered. Grading is idempotent and does not mutate the attempt's
        questions.
        """
        results: list[QuestionResult] = []
        for q in self.questions:
            chosen = responses.get(q.id)
            correct_token = self._correct_tokens[q.id]
            texts = self._token_text[q.id]
            answered = chosen in texts
            results.append(
                QuestionResult(
                    question_id=q.id,
                    number=q.number,
                    category=q.category,
                    text=q.text,
                    chosen_text=texts.get(chosen) if answered else None,
                    correct_text=texts[correct_token],
                    is_correct=answered and chosen == correct_token,
                    answered=answered,
                )
            )
        return ScoreResult.from_results(
            candidate_name=self.candidate_name,
            mode=self.mode,
            time_taken_seconds=max(0, int(finished_at - self.started_at)),
            results=tuple(results),
        )


# --- Results ----------------------------------------------------------------


@dataclass(frozen=True)
class QuestionResult:
    question_id: int
    number: int
    category: str
    text: str
    chosen_text: str | None
    correct_text: str
    is_correct: bool
    answered: bool


@dataclass(frozen=True)
class CategoryScore:
    category: str
    correct: int
    total: int


@dataclass(frozen=True)
class ScoreResult:
    candidate_name: str
    mode: ExamMode
    total: int
    correct: int
    incorrect: int
    unanswered: int
    percentage: float
    time_taken_seconds: int
    categories: tuple[CategoryScore, ...]
    results: tuple[QuestionResult, ...]

    @classmethod
    def from_results(
        cls,
        candidate_name: str,
        mode: ExamMode,
        time_taken_seconds: int,
        results: tuple[QuestionResult, ...],
    ) -> "ScoreResult":
        total = len(results)
        correct = sum(1 for r in results if r.is_correct)
        answered = sum(1 for r in results if r.answered)
        incorrect = answered - correct
        unanswered = total - answered
        percentage = round(correct / total * 100, 1) if total else 0.0

        by_cat: dict[str, list[QuestionResult]] = {}
        for r in results:
            by_cat.setdefault(r.category, []).append(r)
        categories = tuple(
            CategoryScore(
                category=cat,
                correct=sum(1 for r in rs if r.is_correct),
                total=len(rs),
            )
            for cat, rs in sorted(by_cat.items())
        )

        return cls(
            candidate_name=candidate_name,
            mode=mode,
            total=total,
            correct=correct,
            incorrect=incorrect,
            unanswered=unanswered,
            percentage=percentage,
            time_taken_seconds=time_taken_seconds,
            categories=categories,
            results=results,
        )
