# NPF CBT Mock Exam

A timed, multiple-choice Computer-Based Test (CBT) practice app for the
**Nigeria Police Force / Police Service Commission** 2025/2026 exam.

Candidates enter their name, pick a test length, answer shuffled multiple-choice
questions against a countdown, and get a scored breakdown at the end.

## Features

- **Four test modes** — Quick Drill (10q/8m), Short Mock (20q/15m),
  Standard Mock (30q/20m), Full Mock (60q/30m).
- **Shuffled** questions *and* options on every attempt.
- **Countdown timer** with auto-submit when time runs out.
- **Score screen** — percentage, correct/incorrect/unanswered, per-category
  breakdown, and a full answer review.
- **Anti-cheat** — correct answers never leave the server; the browser only
  sees opaque option tokens until the exam is submitted.
- **121 questions** compiled from the source PDF (100 exam + 21 practice).

## Architecture

Clean architecture / DDD, with a clear dependency direction (outer layers
depend on inner, never the reverse):

```
backend/app/
  domain/          # pure business model — no framework, no I/O
    models.py        Question, ExamMode, Attempt (aggregate), ScoreResult
    exam_modes.py    the four selectable modes (business rules)
  application/     # use cases orchestrating the domain
    exam_service.py  start attempt, submit attempt
    ports.py         repository interfaces (Protocols)
    errors.py        expected, user-facing failures
  infrastructure/  # adapters implementing the ports
    question_repository.py   loads questions.json
    attempt_repository.py    in-memory attempt store
    data/questions.json
  api/             # HTTP edge (FastAPI)
    routes.py, schemas.py, dependencies.py
  main.py          # app factory; serves the API and the frontend

frontend/          # vanilla JS + HTML/CSS, no build step
  index.html
  css/styles.css
  js/  api.js · session.js · timer.js · views.js · app.js
```

## Running it

### 1. Backend (also serves the frontend)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Then open **http://localhost:8000** in a browser. That's it — the frontend is
served by the backend, so a single command runs the whole app.

### Run the tests

```bash
cd backend
source .venv/bin/activate
pytest
```

## API

| Method | Path                          | Purpose                                  |
|--------|-------------------------------|------------------------------------------|
| GET    | `/api/modes`                  | List the four exam modes                 |
| POST   | `/api/attempts`               | Start an attempt (`candidate_name`,`mode`) |
| POST   | `/api/attempts/{id}/submit`   | Submit answers, get the score            |
| GET    | `/health`                     | Liveness check                           |

## The answer key

The source PDF has **no answer key**, so answers were derived best-effort. The
23 uncertain/ambiguous/flawed items are documented in
[`ANSWER_KEY_REVIEW.md`](ANSWER_KEY_REVIEW.md). To correct any answer, edit the
`answer` field (letter `A`–`D`) of the question in
`backend/app/infrastructure/data/questions.json` and restart the backend.
