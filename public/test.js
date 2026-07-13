// Testdurchführung: Code eingeben, Fragen beantworten, abschließen.
// Jede Antwort wird sofort per PATCH gespeichert.

"use strict";

const startPanel = document.getElementById("start-panel");
const quizPanel = document.getElementById("quiz-panel");
const donePanel = document.getElementById("done-panel");

let attempt = null;
let currentIndex = 0;
const savedAnswers = {};   // item_id -> selected_option

// Demo-Link auf der Startseite übergibt den Code per URL
const prefilledCode = new URLSearchParams(window.location.search).get("code");
if (prefilledCode) {
  document.getElementById("access-code").value = prefilledCode;
}

document.getElementById("start-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const statusEl = document.getElementById("start-status");
  const code = document.getElementById("access-code").value.trim();
  setStatus(statusEl, "Starte Test …");
  try {
    attempt = await api("POST", "/api/attempts", { access_code: code });
  } catch (err) {
    setStatus(statusEl, err.message, "error");
    return;
  }
  if (attempt.items.length === 0) {
    setStatus(statusEl, "Dieser Test enthält noch keine Fragen.", "error");
    return;
  }
  for (const answer of attempt.answers) {
    savedAnswers[answer.item_id] = answer.selected_option;
  }
  document.getElementById("quiz-heading").textContent = attempt.test_title;
  startPanel.classList.add("hidden");
  quizPanel.classList.remove("hidden");
  showQuestion(0);
});

function showQuestion(index) {
  currentIndex = index;
  const item = attempt.items[index];
  const total = attempt.items.length;

  document.getElementById("question-text").textContent =
    `Frage ${index + 1}: ${item.question}`;
  document.getElementById("progress-text").textContent =
    `Frage ${index + 1} von ${total}`;
  document.getElementById("progress-bar").style.width =
    `${Math.round(((index + 1) / total) * 100)}%`;

  const optionsEl = document.getElementById("options");
  optionsEl.innerHTML = "";
  item.options.forEach((option, i) => {
    const id = `option-${item.id}-${i}`;
    const wrapper = document.createElement("div");
    wrapper.className = "option";

    const input = document.createElement("input");
    input.type = "radio";
    input.name = "answer";
    input.id = id;
    input.value = String(i);
    input.checked = savedAnswers[item.id] === i;
    input.addEventListener("change", () => saveAnswer(item.id, i));

    const label = document.createElement("label");
    label.htmlFor = id;
    label.textContent = option;
    label.style.fontWeight = "normal";
    label.style.margin = "0";

    wrapper.append(input, label);
    optionsEl.append(wrapper);
  });

  document.getElementById("prev-btn").disabled = index === 0;
  const isLast = index === total - 1;
  document.getElementById("next-btn").classList.toggle("hidden", isLast);
  document.getElementById("submit-btn").classList.toggle("hidden", !isLast);
  setStatus(document.getElementById("save-status"), "");
}

async function saveAnswer(itemId, selectedOption) {
  const statusEl = document.getElementById("save-status");
  try {
    await api("PATCH", `/api/attempts/${attempt.id}/answers`, {
      item_id: itemId,
      selected_option: selectedOption,
    });
    savedAnswers[itemId] = selectedOption;
    setStatus(statusEl, "Antwort gespeichert ✓", "ok");
  } catch (err) {
    setStatus(statusEl, `Speichern fehlgeschlagen: ${err.message}`, "error");
  }
}

document.getElementById("prev-btn").addEventListener("click", () => {
  if (currentIndex > 0) showQuestion(currentIndex - 1);
});

document.getElementById("next-btn").addEventListener("click", () => {
  if (currentIndex < attempt.items.length - 1) showQuestion(currentIndex + 1);
});

document.getElementById("submit-btn").addEventListener("click", async () => {
  const statusEl = document.getElementById("save-status");
  const unanswered = attempt.items.length - Object.keys(savedAnswers).length;
  if (unanswered > 0) {
    const proceed = window.confirm(
      `Es sind noch ${unanswered} Frage(n) unbeantwortet. Trotzdem abschließen?`
    );
    if (!proceed) return;
  }
  try {
    const result = await api("POST", `/api/attempts/${attempt.id}/submit`);
    document.getElementById("done-text").textContent =
      `Deine Antworten wurden übermittelt (Durchlauf-Nr. ${result.id}).`;
    quizPanel.classList.add("hidden");
    donePanel.classList.remove("hidden");
    document.getElementById("done-heading").focus?.();
  } catch (err) {
    setStatus(statusEl, `Abschließen fehlgeschlagen: ${err.message}`, "error");
  }
});
