"""Loads the question bank from the bundled JSON file.

The file is read once and cached; questions never change at runtime.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ..domain.models import Choice, Question

DATA_FILE = Path(__file__).parent / "data" / "questions.json"


class JsonQuestionRepository:
    def __init__(self, data_file: Path = DATA_FILE) -> None:
        self._data_file = data_file

    @lru_cache(maxsize=1)
    def all(self) -> list[Question]:
        raw = json.loads(self._data_file.read_text(encoding="utf-8"))
        return [self._to_question(item) for item in raw]

    @staticmethod
    def _to_question(item: dict) -> Question:
        return Question(
            id=item["id"],
            number=item["number"],
            category=item["category"],
            text=item["text"],
            choices=tuple(Choice(c["key"], c["text"]) for c in item["choices"]),
            answer=item["answer"],
            confidence=item.get("confidence", "high"),
            note=item.get("note", ""),
            practice=item.get("practice", False),
        )
