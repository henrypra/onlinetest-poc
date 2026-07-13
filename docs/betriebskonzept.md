# Betriebskonzept – Kompetenzerfassung Online (Beta)

Stand: Juli 2026 · Gilt für Version 0.2.0

## 1. Systemübersicht

Eine einzelne Python-Anwendung (FastAPI + Uvicorn) liefert REST-API **und**
statisches Frontend aus. Persistenz über eine SQLite-Datei – kein separater
Datenbankserver, kein Message-Broker, keine weiteren Dienste.

```
Browser ──HTTPS──> Uvicorn/FastAPI ──> SQLite-Datei (onlinetest.db)
                    ├── /            statisches Frontend (public/)
                    ├── /api/...     REST-API
                    └── /docs        OpenAPI-Doku (automatisch generiert)
```

## 2. Deployment

### 2.1 Lokal (Entwicklung)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Die App läuft auf `http://127.0.0.1:8000`, die Datenbankdatei `onlinetest.db`
wird beim ersten Start automatisch im Projektverzeichnis angelegt.

### 2.2 Render.com (Free Tier, empfohlen für die Beta)

1. Repository zu GitHub pushen.
2. Auf [render.com](https://render.com) → **New → Blueprint** → Repository wählen.
   Render liest `render.yaml` und konfiguriert den Service automatisch
   (Build: `pip install -r requirements.txt`, Start: `uvicorn app.main:app
   --host 0.0.0.0 --port $PORT`, Healthcheck: `/api/health`).
3. HTTPS stellt Render automatisch bereit.

**Free-Tier-Eigenheiten:**
- Der Dienst schläft nach 15 Minuten Inaktivität ein; der erste Request danach
  dauert ~30–60 s (Cold Start).
- Keine persistente Disk im Free-Plan: Die SQLite-Datei wird bei jedem
  Deploy/Neustart zurückgesetzt. Für Demos ausreichend; für dauerhafte Daten
  Starter-Plan mit Disk (siehe Kommentar in `render.yaml`) und
  `DATABASE_URL=sqlite:////data/onlinetest.db` setzen.

### 2.3 Alternative: Fly.io

Kleine VM aus der Free Allowance plus 1-GB-Volume für die SQLite-Datei
(`fly launch`, Volume nach `/data` mounten, `DATABASE_URL` entsprechend setzen).

## 3. Konfiguration

| Umgebungsvariable | Standard | Zweck |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./onlinetest.db` | Pfad/URL der Datenbank (z. B. Volume-Pfad im Hosting) |
| `DEMO_ACCESS_CODE` | `ZFH2VVKZ` | Zugangscode des automatisch angelegten Demo-Tests; leerer Wert deaktiviert das Seeding |
| `PORT` (nur Hosting) | 8000 | Wird von der Plattform gesetzt, an Uvicorn durchgereicht |

## 4. Monitoring & Logging

- **Health-Check:** `GET /api/health` → `{"status": "ok"}` (in `render.yaml`
  als Healthcheck hinterlegt; extern z. B. mit UptimeRobot kostenlos überwachbar).
- **Logging:** Python-`logging` auf stdout (Render/Fly sammeln stdout automatisch).
  Geloggt werden u. a.: App-Start, angelegte Tests/Items, gestartete und
  abgeschlossene Durchläufe (mit Score), ungültige Zugangscodes (WARNING).
- Fehlerbilder sind über eindeutige HTTP-Statuscodes unterscheidbar:
  404 (nicht gefunden / ungültiger Code), 409 (bereits abgeschlossen),
  422 (Validierungsfehler mit Detailmeldung).

## 5. Backup & Wiederherstellung

Die gesamte Persistenz ist **eine Datei** – Backup = Datei kopieren:

```bash
# Backup (lokal oder per SSH/Konsole der Hosting-Plattform)
sqlite3 onlinetest.db ".backup 'backup-$(date +%F).db'"

# Wiederherstellung: App stoppen, Datei zurückkopieren, App starten
cp backup-2026-07-13.db onlinetest.db
```

`sqlite3 .backup` ist auch bei laufender App konsistent (Online-Backup-API).
Empfehlung für Dauerbetrieb: tägliches Backup per Cronjob, Aufbewahrung 14 Tage.

## 6. Wartung & Support (2nd/3rd Level)

- **Troubleshooting-Leitfaden:** siehe README, Abschnitt "Troubleshooting"
  (häufige Fehlerbilder mit Ursache und Lösung).
- **Updates:** Abhängigkeiten sind in `requirements.txt` gepinnt.
  Update-Prozess: Version anheben → `pytest` lokal → deployen.
- **API-Änderungen:** Nach jeder Schnittstellenänderung
  `python scripts/export_openapi.py` ausführen, damit `openapi.yaml` als
  dokumentierter Vertrag aktuell bleibt (relevant für externe Dienstleister,
  die gegen die API integrieren).

## 7. Skalierungsgrenzen (bewusst akzeptiert)

SQLite + ein Uvicorn-Prozess trägt problemlos Schulklassen-Last (dutzende
gleichzeitige Teilnehmer:innen, überwiegend kleine Schreiboperationen).
Bei landesweitem Einsatz wäre der Migrationspfad: PostgreSQL statt SQLite
(SQLModel/SQLAlchemy machen das zu einer Konfigurationsänderung) und mehrere
Uvicorn-Worker hinter einem Load Balancer.
