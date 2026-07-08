// Pure-ish rendering: each function reads app data and updates the DOM.
// Event wiring lives in app.js; these functions receive callbacks.

import { formatClock } from "./timer.js";

const $ = (id) => document.getElementById(id);
const LETTERS = ["A", "B", "C", "D", "E", "F"];

// ---- view switching -------------------------------------------------------

export function showView(name) {
  for (const el of document.querySelectorAll(".view")) {
    el.classList.toggle("is-active", el.id === `view-${name}`);
  }
  window.scrollTo(0, 0);
}

// ---- welcome --------------------------------------------------------------

export function renderModes(modes, selectedCode, onSelect) {
  const list = $("mode-list");
  list.innerHTML = "";
  for (const mode of modes) {
    const mins = Math.round(mode.duration_seconds / 60);
    const card = document.createElement("button");
    card.type = "button";
    card.className = "mode-card" + (mode.code === selectedCode ? " selected" : "");
    card.setAttribute("role", "radio");
    card.setAttribute("aria-checked", mode.code === selectedCode);
    card.innerHTML = `
      <div class="mode-name">${escapeHtml(mode.label)}</div>
      <div class="mode-detail">${mode.question_count} questions &middot; ${mins} min</div>
    `;
    card.addEventListener("click", () => onSelect(mode.code));
    list.appendChild(card);
  }
}

export function showWelcomeError(message) {
  const el = $("welcome-error");
  if (message) {
    el.textContent = message;
    el.hidden = false;
  } else {
    el.hidden = true;
  }
}

// ---- exam header ----------------------------------------------------------

export function renderExamHeader(session) {
  $("exam-candidate").textContent = session.candidateName;
  $("exam-mode").textContent = session.mode.label;
  $("total-count").textContent = session.total;
  updateProgress(session);
}

export function updateProgress(session) {
  $("answered-count").textContent = session.answeredCount;
}

export function renderTimer(remainingSeconds, durationSeconds) {
  const el = $("timer");
  el.textContent = formatClock(remainingSeconds);
  el.classList.toggle("warning", remainingSeconds <= 60 && remainingSeconds > 20);
  el.classList.toggle("danger", remainingSeconds <= 20);
}

// ---- question + navigator -------------------------------------------------

export function renderQuestion(session, onSelectChoice) {
  const q = session.current;
  $("q-number").textContent = q.number;
  $("q-category").textContent = q.category;
  $("q-text").textContent = q.text;

  const chosen = session.chosenToken(q.id);
  const container = $("q-choices");
  container.innerHTML = "";

  q.choices.forEach((choice, idx) => {
    const el = document.createElement("button");
    el.type = "button";
    el.className = "choice" + (choice.token === chosen ? " selected" : "");
    el.innerHTML = `
      <span class="choice-letter">${LETTERS[idx]}</span>
      <span class="choice-text">${escapeHtml(choice.text)}</span>
    `;
    el.addEventListener("click", () => onSelectChoice(q.id, choice.token));
    container.appendChild(el);
  });

  $("prev-btn").disabled = session.currentIndex === 0;
  $("next-btn").disabled = session.currentIndex === session.total - 1;
}

export function renderNavigator(session, onNavigate) {
  const grid = $("nav-grid");
  grid.innerHTML = "";
  session.questions.forEach((q, idx) => {
    const cell = document.createElement("button");
    cell.type = "button";
    cell.className = "nav-cell";
    if (session.isAnswered(q.id)) cell.classList.add("answered");
    if (idx === session.currentIndex) cell.classList.add("current");
    cell.textContent = q.number;
    cell.addEventListener("click", () => onNavigate(idx));
    grid.appendChild(cell);
  });
}

// ---- results --------------------------------------------------------------

export function renderResults(score, onRestart) {
  $("results-name").textContent = `Well done, ${score.candidate_name.split(" ")[0]}!`;
  $("results-verdict").textContent = verdict(score.percentage);
  $("results-meta").textContent =
    `${score.mode.label} · ${score.total} questions · time taken ${formatClock(
      score.time_taken_seconds
    )}`;

  const ring = $("score-ring");
  ring.style.setProperty("--pct", `${score.percentage}%`);
  $("score-percent").textContent = `${Math.round(score.percentage)}%`;

  $("stat-correct").textContent = score.correct;
  $("stat-incorrect").textContent = score.incorrect;
  $("stat-unanswered").textContent = score.unanswered;

  const breakdown = $("category-breakdown");
  breakdown.innerHTML = "";
  for (const cat of score.categories) {
    const pct = cat.total ? Math.round((cat.correct / cat.total) * 100) : 0;
    const row = document.createElement("div");
    row.className = "cat-row";
    row.innerHTML = `
      <div class="cat-row-head">
        <span>${escapeHtml(cat.category)}</span>
        <span>${cat.correct}/${cat.total}</span>
      </div>
      <div class="cat-bar"><span style="width:${pct}%"></span></div>
    `;
    breakdown.appendChild(row);
  }

  const reviewList = $("review-list");
  reviewList.innerHTML = "";
  for (const item of score.review) {
    const el = document.createElement("div");
    el.className = "review-item";
    const tag = item.is_correct
      ? '<span class="review-tag ok">Correct</span>'
      : item.answered
      ? '<span class="review-tag no">Wrong</span>'
      : '<span class="review-tag skip">Skipped</span>';
    const yourAnswer = item.answered
      ? `<span class="review-a ${item.is_correct ? "right" : "wrong"}">Your answer: ${escapeHtml(
          item.chosen_text
        )}</span>`
      : `<span class="review-a">Your answer: —</span>`;
    const correct = item.is_correct
      ? ""
      : `<span class="review-a right">Correct answer: ${escapeHtml(item.correct_text)}</span>`;
    el.innerHTML = `
      <div class="review-q">${tag}Q${item.number}. ${escapeHtml(item.text)}</div>
      ${yourAnswer}
      ${correct}
    `;
    reviewList.appendChild(el);
  }

  $("restart-btn").onclick = onRestart;
}

function verdict(pct) {
  if (pct >= 70) return "Excellent — you're exam ready.";
  if (pct >= 50) return "A solid pass. Keep practising.";
  if (pct >= 40) return "Almost there — review your weak areas.";
  return "Keep going — more practice will help.";
}

// ---- utilities ------------------------------------------------------------

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
