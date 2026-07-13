"""Tests für die Demo-Daten (fester Zugangscode für den Beispieltest)."""

import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app import models
from app.models import Item
from app.seed import DEMO_ACCESS_CODE, seed_demo_data


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_seed_creates_demo_test(session):
    seed_demo_data(session)

    test = session.exec(
        select(models.Test).where(models.Test.access_code == DEMO_ACCESS_CODE)
    ).first()
    assert test is not None
    assert DEMO_ACCESS_CODE == "ZFH2VVKZ"

    items = session.exec(select(Item).where(Item.test_id == test.id)).all()
    assert len(items) == 5
    for item in items:
        assert 0 <= item.correct_option < len(item.options)


def test_seed_is_idempotent(session):
    seed_demo_data(session)
    seed_demo_data(session)

    tests = session.exec(
        select(models.Test).where(models.Test.access_code == DEMO_ACCESS_CODE)
    ).all()
    assert len(tests) == 1


def test_demo_code_starts_attempt(client):
    """Der Demo-Test ist über die API tatsächlich durchführbar."""
    # Seeding in die Test-DB (die App-Lifespan seedet nur die echte Engine)
    from app.db import get_session
    from app.main import app

    override = app.dependency_overrides[get_session]
    session = next(override())
    seed_demo_data(session)

    response = client.post("/api/attempts", json={"access_code": "ZFH2VVKZ"})
    assert response.status_code == 201
    assert len(response.json()["items"]) == 5
