"""Gemeinsame Test-Fixtures: frische In-Memory-SQLite-DB pro Testfunktion."""

import os

# Vor dem App-Import setzen: Die Lifespan legt sonst beim TestClient-Start
# Tabellen in der echten onlinetest.db an.
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db import get_session
from app.main import app


@pytest.fixture
def client():
    # In-Memory-DB mit StaticPool: alle Verbindungen teilen sich dieselbe DB.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_test(client):
    """Legt einen Test mit zwei Fragen an und liefert die API-Antwort (inkl. Code)."""
    test = client.post(
        "/api/tests", json={"title": "Mathe Basis", "description": "Brüche"}
    ).json()
    client.post(
        f"/api/tests/{test['id']}/items",
        json={
            "question": "Was ist 1/2 + 1/4?",
            "options": ["3/4", "2/6", "1/8"],
            "correct_option": 0,
        },
    )
    client.post(
        f"/api/tests/{test['id']}/items",
        json={
            "question": "Was ist 2/3 von 9?",
            "options": ["3", "6", "9"],
            "correct_option": 1,
        },
    )
    return client.get(f"/api/tests/{test['id']}").json()
