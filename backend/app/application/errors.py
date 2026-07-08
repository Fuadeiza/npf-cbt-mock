"""Application-level errors, mapped to HTTP responses at the edge."""
from __future__ import annotations


class ApplicationError(Exception):
    """Base class for expected, user-facing failures."""


class ModeNotFound(ApplicationError):
    pass


class AttemptNotFound(ApplicationError):
    pass


class AttemptAlreadySubmitted(ApplicationError):
    pass


class InvalidCandidateName(ApplicationError):
    pass


class NotEnoughQuestions(ApplicationError):
    pass
