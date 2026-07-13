import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from app.db import create_db_and_tables, engine
from app.routers import attempts, tests
from app.seed import seed_demo_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("onlinetest")


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        seed_demo_data(session)
    logger.info("Datenbank initialisiert, App bereit")
    yield


app = FastAPI(
    title="Kompetenzerfassung Online (Beta)",
    description=(
        "Webbasiertes Tool zur Durchführung von Onlinetests zur Kompetenzerfassung. "
        "Teilnahme anonym per Zugangscode. Beta-Version – ein Testprojekt von "
        "Henry Pratsch."
    ),
    version="0.2.0",
    contact={"name": "Henry Pratsch"},
    lifespan=lifespan,
)

app.include_router(tests.router)
app.include_router(attempts.router)


@app.get("/api/health", tags=["betrieb"])
def health():
    """Health-Check für Monitoring."""
    return {"status": "ok"}


# zuletzt mounten, damit die /api-Routen Vorrang haben
app.mount("/", StaticFiles(directory="public", html=True), name="frontend")
