// Verwaltungsseite: Testübersicht, Test anlegen, Fragen hinzufügen, Auswertung.

"use strict";

let currentTest = null;

async function loadTestList() {
  const rows = document.getElementById("test-list-rows");
  const select = document.getElementById("results-test-select");
  const statusEl = document.getElementById("test-list-status");
  let tests;
  try {
    tests = await api("GET", "/api/tests");
  } catch (err) {
    setStatus(statusEl, err.message, "error");
    return;
  }

  rows.innerHTML = "";
  if (tests.length === 0) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 5;
    td.className = "muted";
    td.textContent = "Noch keine Tests vorhanden – unten einen anlegen.";
    tr.append(td);
    rows.append(tr);
  }
  for (const test of tests) {
    const tr = document.createElement("tr");
    for (const text of [`${test.id}`, test.title, test.access_code, `${test.item_count}`]) {
      const td = document.createElement("td");
      if (text === test.access_code) {
        const code = document.createElement("code");
        code.className = "inline-code";
        code.textContent = text;
        td.append(code);
      } else {
        td.textContent = text;
      }
      tr.append(td);
    }
    const actions = document.createElement("td");
    const editBtn = document.createElement("button");
    editBtn.type = "button";
    editBtn.className = "secondary small";
    editBtn.textContent = "Fragen bearbeiten";
    editBtn.addEventListener("click", () => openItemEditor(test.id));
    const resultsBtn = document.createElement("button");
    resultsBtn.type = "button";
    resultsBtn.className = "secondary small";
    resultsBtn.textContent = "Auswerten";
    resultsBtn.style.marginLeft = "0.4rem";
    resultsBtn.addEventListener("click", () => {
      select.value = String(test.id);
      showResults(test.id);
    });
    actions.append(editBtn, resultsBtn);
    tr.append(actions);
    rows.append(tr);
  }

  const previous = select.value;
  select.innerHTML = '<option value="">– bitte wählen –</option>';
  for (const test of tests) {
    const option = document.createElement("option");
    option.value = String(test.id);
    option.textContent = `${test.title} (ID ${test.id}, ${test.item_count} Fragen)`;
    select.append(option);
  }
  select.value = previous;
}

async function openItemEditor(testId) {
  currentTest = await api("GET", `/api/tests/${testId}`);
  document.getElementById("item-panel").classList.remove("hidden");
  updateItemCount();
  document.getElementById("item-panel").scrollIntoView({ behavior: "smooth" });
  document.getElementById("item-question").focus();
}

document.getElementById("create-test-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const statusEl = document.getElementById("create-status");
  setStatus(statusEl, "Lege Test an …");
  try {
    currentTest = await api("POST", "/api/tests", {
      title: document.getElementById("test-title").value.trim(),
      description: document.getElementById("test-description").value.trim(),
    });
  } catch (err) {
    setStatus(statusEl, err.message, "error");
    return;
  }
  setStatus(statusEl, `Test angelegt (ID ${currentTest.id}).`, "ok");
  document.getElementById("access-code-display").textContent = currentTest.access_code;
  document.getElementById("test-created").classList.remove("hidden");
  document.getElementById("item-panel").classList.remove("hidden");
  updateItemCount();
  loadTestList();
});

const optionInputsEl = document.getElementById("option-inputs");

function addOptionRow(focus = false) {
  const index = optionInputsEl.children.length;
  const row = document.createElement("div");
  row.className = "option";

  const radio = document.createElement("input");
  radio.type = "radio";
  radio.name = "correct-option";
  radio.value = String(index);
  radio.title = "Als richtige Antwort markieren";
  if (index === 0) radio.checked = true;

  const input = document.createElement("input");
  input.type = "text";
  input.required = true;
  input.placeholder = `Option ${index + 1}`;
  input.setAttribute("aria-label", `Antwortoption ${index + 1}`);

  row.append(radio, input);
  optionInputsEl.append(row);
  if (focus) input.focus();
}

function resetOptionRows() {
  optionInputsEl.innerHTML = "";
  addOptionRow();
  addOptionRow();
}

function updateItemCount() {
  document.getElementById("item-count").textContent =
    `Test „${currentTest.title}" (ID ${currentTest.id}) – ${currentTest.items.length} Frage(n) bisher.`;
}

document.getElementById("add-option-btn").addEventListener("click", () => {
  if (optionInputsEl.children.length < 10) addOptionRow(true);
});

document.getElementById("add-item-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const statusEl = document.getElementById("item-status");
  const options = [...optionInputsEl.querySelectorAll("input[type=text]")]
    .map((input) => input.value.trim())
    .filter((value) => value.length > 0);
  const correct = optionInputsEl.querySelector("input[type=radio]:checked");

  if (options.length < 2) {
    setStatus(statusEl, "Bitte mindestens zwei Antwortoptionen angeben.", "error");
    return;
  }
  try {
    const item = await api("POST", `/api/tests/${currentTest.id}/items`, {
      question: document.getElementById("item-question").value.trim(),
      options,
      correct_option: Number(correct.value),
    });
    currentTest.items.push(item);
    setStatus(statusEl, `Frage ${item.position} gespeichert ✓`, "ok");
    document.getElementById("item-question").value = "";
    resetOptionRows();
    updateItemCount();
    loadTestList();
    document.getElementById("item-question").focus();
  } catch (err) {
    setStatus(statusEl, err.message, "error");
  }
});

resetOptionRows();

document.getElementById("results-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const testId = document.getElementById("results-test-select").value;
  if (testId) showResults(testId);
});

async function showResults(testId) {
  const statusEl = document.getElementById("results-status");
  setStatus(statusEl, "Lade Ergebnisse …");
  let results;
  try {
    results = await api("GET", `/api/tests/${testId}/results`);
  } catch (err) {
    setStatus(statusEl, err.message, "error");
    document.getElementById("results-output").classList.add("hidden");
    return;
  }
  setStatus(statusEl, "");
  document.getElementById("results-title").textContent =
    `${results.test_title} (max. ${results.max_score} Punkte)`;

  document.getElementById("results-summary").textContent =
    results.submitted_count === 0
      ? "Noch keine abgeschlossenen Durchläufe."
      : `${results.submitted_count} abgeschlossene(r) Durchlauf/Durchläufe · ` +
        `Durchschnitt: ${results.average_score} von ${results.max_score} Punkten`;

  renderDistributionChart(results);
  renderResultsTable(results);
  document.getElementById("results-output").classList.remove("hidden");
  document.getElementById("results-output").scrollIntoView({ behavior: "smooth" });
}

// Säulendiagramm der Punkteverteilung, die Tabelle darunter bleibt
// als barrierefreie Alternative.
function renderDistributionChart(results) {
  const block = document.getElementById("chart-block");
  const chart = document.getElementById("results-chart");
  const labels = document.getElementById("results-chart-labels");

  if (results.submitted_count === 0 || results.max_score === 0) {
    block.classList.add("hidden");
    return;
  }
  block.classList.remove("hidden");

  const counts = [];
  for (let score = 0; score <= results.max_score; score++) {
    counts.push(results.score_distribution[String(score)] ?? 0);
  }
  const maxCount = Math.max(...counts, 1);

  chart.innerHTML = "";
  labels.innerHTML = "";
  chart.setAttribute(
    "aria-label",
    "Punkteverteilung: " +
      counts.map((count, score) => `${score} Punkte: ${count}`).join(", ")
  );

  counts.forEach((count, score) => {
    const col = document.createElement("div");
    col.className = "col";
    col.title = `${score} Punkte: ${count} Teilnahme(n)`;

    const value = document.createElement("span");
    value.className = "value";
    value.textContent = count > 0 ? String(count) : "";

    const bar = document.createElement("div");
    bar.className = "bar" + (count === 0 ? " zero" : "");
    bar.style.height = count === 0 ? "2px" : `${Math.round((count / maxCount) * 100)}%`;

    col.append(value, bar);
    chart.append(col);

    const label = document.createElement("span");
    label.textContent = String(score);
    labels.append(label);
  });
}

function renderResultsTable(results) {
  const rows = document.getElementById("results-rows");
  rows.innerHTML = "";
  for (const entry of results.attempts) {
    const tr = document.createElement("tr");
    const started = new Date(entry.started_at).toLocaleString("de-DE");
    const status = entry.submitted_at ? "abgeschlossen" : "läuft / abgebrochen";
    const score = entry.score === null ? "–" : `${entry.score} / ${entry.max_score}`;
    for (const text of [`#${entry.attempt_id}`, started, status, score]) {
      const td = document.createElement("td");
      td.textContent = text;
      tr.append(td);
    }
    rows.append(tr);
  }
}

loadTestList().then(() => {
  // Direktlink zur Auswertung: admin.html?results=<test_id>
  const resultsParam = new URLSearchParams(window.location.search).get("results");
  if (resultsParam) {
    document.getElementById("results-test-select").value = resultsParam;
    showResults(resultsParam);
  }
});
