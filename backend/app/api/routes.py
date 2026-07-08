"""HTTP routes for the exam. Thin adapters over :class:`ExamService`."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..application.errors import (
    ApplicationError,
    AttemptAlreadySubmitted,
    AttemptNotFound,
)
from ..application.exam_service import ExamService
from .dependencies import get_exam_service
from .schemas import ModeOut, ScoreResponse, StartRequest, StartResponse, SubmitRequest

router = APIRouter(prefix="/api")


@router.get("/modes", response_model=list[ModeOut])
def list_modes(service: ExamService = Depends(get_exam_service)) -> list[ModeOut]:
    return [ModeOut.of(m) for m in service.list_modes()]


@router.post("/attempts", response_model=StartResponse)
def start_attempt(
    body: StartRequest, service: ExamService = Depends(get_exam_service)
) -> StartResponse:
    try:
        attempt = service.start_attempt(body.candidate_name, body.mode)
    except ApplicationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return StartResponse.of(attempt)


@router.post("/attempts/{attempt_id}/submit", response_model=ScoreResponse)
def submit_attempt(
    attempt_id: str,
    body: SubmitRequest,
    service: ExamService = Depends(get_exam_service),
) -> ScoreResponse:
    try:
        result = service.submit_attempt(attempt_id, body.answers)
    except AttemptNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AttemptAlreadySubmitted as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ApplicationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ScoreResponse.of(result)
