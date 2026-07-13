# Sicherheitskonzept – Kompetenzerfassung Online (Beta)

Stand: Juli 2026 · Gilt für Version 0.2.0

## 1. Schutzziel und Datensparsamkeit

Das Tool erfasst Kompetenzen von Schülerinnen und Schülern. Oberstes Prinzip ist
**Datensparsamkeit**: Es werden **keine personenbezogenen Daten** erhoben.

- Teilnahme erfolgt **anonym per Zugangscode** – keine Namen, keine E-Mail-Adressen,
  keine Accounts, keine IP-Speicherung in der Datenbank.
- Ein Testdurchlauf (Attempt) ist nur über eine fortlaufende, nicht sprechende ID
  identifizierbar. Eine Zuordnung zu einer Person ist systemseitig nicht möglich
  (und für die Beta nicht vorgesehen).
- Gespeichert werden ausschließlich: Testdefinitionen, gewählte Antwortoptionen,
  Zeitstempel und Scores.

## 2. Zugangscodes

- Codes werden serverseitig mit `secrets.choice` erzeugt (kryptografisch sicherer
  Zufall, kein `random`).
- 8 Zeichen aus einem 31-Zeichen-Alphabet (ohne verwechselbare Zeichen 0/O/1/I/L)
  ergeben ≈ 31⁸ ≈ 8,5 × 10¹¹ Kombinationen – Raten ist praktisch aussichtslos.
- Eindeutigkeit wird per Unique-Constraint in der Datenbank erzwungen.

## 3. Input-Validierung

- Alle Requests werden serverseitig über **Pydantic-Schemas** validiert
  (Typen, Pflichtfelder, Längen-Limits). Ungültige Eingaben führen zu HTTP 422
  mit klarer Fehlermeldung – sie erreichen die Datenbank nie.
- Zusätzliche fachliche Prüfungen im Code:
  - `correct_option` / `selected_option` müssen auf eine existierende Option zeigen.
  - Antworten werden nur für Fragen des eigenen Tests akzeptiert (kein
    Cross-Test-Zugriff über fremde `item_id`).
  - Abgeschlossene Durchläufe sind unveränderlich (HTTP 409 bei erneutem
    Submit oder nachträglichen Antworten).
- Datenbankzugriff ausschließlich über SQLModel/SQLAlchemy mit gebundenen
  Parametern – **kein SQL-Injection-Risiko** durch String-Konkatenation.
- Das Frontend rendert Inhalte über `textContent`/DOM-APIs, nicht über
  `innerHTML` mit Nutzdaten – **kein XSS** durch Fragen- oder Antworttexte.

## 4. Schutz der Lösungen

- Die richtige Antwort (`correct_option`) wird Teilnehmer:innen **nie**
  ausgeliefert: Die Schüler-Endpunkte nutzen ein eigenes Response-Schema
  (`ItemPublic`) ohne dieses Feld. Ein API-Test sichert das explizit ab.
- Die Bewertung (Score) wird ausschließlich **serverseitig** berechnet.

## 5. Transportverschlüsselung

- In Produktion (Render.com / Fly.io) wird **HTTPS automatisch** durch die
  Plattform bereitgestellt (verwaltete TLS-Zertifikate, HTTP→HTTPS-Redirect).
- Lokal läuft die App nur zur Entwicklung über HTTP auf `127.0.0.1`.

## 6. Bekannte Einschränkungen der Beta (bewusste Entscheidungen)

| Einschränkung | Begründung / Ausbaustufe |
|---|---|
| Admin-Endpunkte ohne Authentifizierung | In der Beta bewusst ausgeklammert. Ausbaustufe: API-Key oder OAuth2/OIDC (FastAPI bringt `Security`-Utilities mit). |
| Kein Rate-Limiting | Bei öffentlichem Dauerbetrieb wäre z. B. `slowapi` oder ein vorgeschalteter Proxy sinnvoll (Brute-Force auf Zugangscodes weiter erschweren). |
| SQLite ohne Verschlüsselung at rest | Es liegen keine personenbezogenen Daten vor; bei höherem Schutzbedarf: verschlüsseltes Volume oder PostgreSQL. |

## 7. Abhängigkeiten

- Bewusst minimaler Stack (FastAPI, SQLModel, Uvicorn) – kleine Angriffsfläche.
- Versionen sind in `requirements.txt` gepinnt; Updates werden bewusst eingespielt
  (z. B. via `pip list --outdated` oder Dependabot).
