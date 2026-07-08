// Holds the state of the exam sitting in the browser: the questions, the
// candidate's chosen token per question, and which question is on screen.

export class ExamSession {
  constructor(attempt) {
    this.attemptId = attempt.attempt_id;
    this.candidateName = attempt.candidate_name;
    this.mode = attempt.mode;
    this.durationSeconds = attempt.duration_seconds;
    this.questions = attempt.questions;
    this.answers = new Map(); // question id -> chosen token
    this.currentIndex = 0;
  }

  get current() {
    return this.questions[this.currentIndex];
  }

  get total() {
    return this.questions.length;
  }

  get answeredCount() {
    return this.answers.size;
  }

  select(questionId, token) {
    this.answers.set(questionId, token);
  }

  chosenToken(questionId) {
    return this.answers.get(questionId) ?? null;
  }

  isAnswered(questionId) {
    return this.answers.has(questionId);
  }

  goTo(index) {
    if (index >= 0 && index < this.total) this.currentIndex = index;
  }

  next() {
    this.goTo(this.currentIndex + 1);
  }

  prev() {
    this.goTo(this.currentIndex - 1);
  }

  // Plain object for the submit payload: { questionId: token }.
  toAnswerPayload() {
    return Object.fromEntries(this.answers);
  }
}
