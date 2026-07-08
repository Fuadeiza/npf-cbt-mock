// Controller: wires the DOM, API, session state, and timer together and
// drives the three screens (welcome -> exam -> results).

import { api } from "./api.js";
import { ExamSession } from "./session.js";
import { CountdownTimer } from "./timer.js";
import * as views from "./views.js";

const $ = (id) => document.getElementById(id);

const app = {
  modes: [],
  selectedMode: null,
  session: null,
  timer: null,
  submitting: false,
};

// ---- welcome --------------------------------------------------------------

async function initWelcome() {
  try {
    app.modes = await api.listModes();
  } catch (err) {
    views.showWelcomeError("Could not reach the exam server. Is the backend running?");
    return;
  }
  app.selectedMode = app.modes[0]?.code ?? null;
  views.renderModes(app.modes, app.selectedMode, selectMode);
}

function selectMode(code) {
  app.selectedMode = code;
  views.renderModes(app.modes, app.selectedMode, selectMode);
}

async function startExam() {
  const name = $("candidate-name").value.trim();
  if (!name) {
    views.showWelcomeError("Please enter your name to begin.");
    $("candidate-name").focus();
    return;
  }
  if (!app.selectedMode) {
    views.showWelcomeError("Please choose a test.");
    return;
  }
  views.showWelcomeError(null);
  $("start-btn").disabled = true;

  try {
    const attempt = await api.startAttempt(name, app.selectedMode);
    beginSession(attempt);
  } catch (err) {
    views.showWelcomeError(err.message);
  } finally {
    $("start-btn").disabled = false;
  }
}

// ---- exam -----------------------------------------------------------------

function beginSession(attempt) {
  app.session = new ExamSession(attempt);
  app.submitting = false;

  views.renderExamHeader(app.session);
  redrawQuestion();
  views.showView("exam");

  app.timer = new CountdownTimer(app.session.durationSeconds, {
    onTick: (remaining) => views.renderTimer(remaining, app.session.durationSeconds),
    onExpire: () => submitExam(true),
  });
  app.timer.start();
}

function redrawQuestion() {
  views.renderQuestion(app.session, onSelectChoice);
  views.renderNavigator(app.session, onNavigate);
}

function onSelectChoice(questionId, token) {
  app.session.select(questionId, token);
  views.updateProgress(app.session);
  redrawQuestion();
}

function onNavigate(index) {
  app.session.goTo(index);
  redrawQuestion();
}

function goNext() {
  app.session.next();
  redrawQuestion();
}

function goPrev() {
  app.session.prev();
  redrawQuestion();
}

async function submitExam(auto = false) {
  if (app.submitting) return;
  if (!auto) {
    const remaining = app.session.total - app.session.answeredCount;
    const message =
      remaining > 0
        ? `You have ${remaining} unanswered question(s). Submit anyway?`
        : "Submit your exam now?";
    if (!window.confirm(message)) return;
  }

  app.submitting = true;
  app.timer?.stop();
  $("submit-btn").disabled = true;

  try {
    const score = await api.submitAttempt(
      app.session.attemptId,
      app.session.toAnswerPayload()
    );
    showResults(score);
  } catch (err) {
    window.alert(`Could not submit: ${err.message}`);
    app.submitting = false;
    $("submit-btn").disabled = false;
  }
}

// ---- results --------------------------------------------------------------

function showResults(score) {
  views.renderResults(score, restart);
  views.showView("results");
}

function restart() {
  app.session = null;
  app.timer = null;
  $("candidate-name").value = "";
  $("submit-btn").disabled = false;
  views.showView("welcome");
  $("candidate-name").focus();
}

// ---- bootstrap ------------------------------------------------------------

function bindEvents() {
  $("start-btn").addEventListener("click", startExam);
  $("candidate-name").addEventListener("keydown", (e) => {
    if (e.key === "Enter") startExam();
  });
  $("next-btn").addEventListener("click", goNext);
  $("prev-btn").addEventListener("click", goPrev);
  $("submit-btn").addEventListener("click", () => submitExam(false));
}

bindEvents();
initWelcome();
