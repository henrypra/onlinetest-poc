// Gemeinsamer API-Helfer für Admin- und Testseite.

"use strict";

async function api(method, path, body) {
  let response;
  try {
    response = await fetch(path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Server nicht erreichbar. Bitte Verbindung prüfen.");
  }

  if (!response.ok) {
    let detail = `Fehler ${response.status}`;
    try {
      const data = await response.json();
      if (typeof data.detail === "string") detail = data.detail;
    } catch { /* kein JSON, Standardmeldung reicht */ }
    throw new Error(detail);
  }
  return response.json();
}

function setStatus(element, message, type) {
  element.textContent = message;
  element.className = "status" + (type ? " " + type : "");
}
