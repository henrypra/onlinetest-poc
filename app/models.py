from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Test(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str = ""
    access_code: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=utcnow)


class Item(SQLModel, table=True):
    """Multiple-Choice-Frage. Optionen liegen als JSON-Liste in einer Spalte,
    das spart eine eigene Options-Tabelle."""

    id: int | None = Field(default=None, primary_key=True)
    test_id: int = Field(foreign_key="test.id", index=True)
    position: int
    question: str
    options: list[str] = Field(sa_column=Column(JSON))
    correct_option: int  # Index in options


class Attempt(SQLModel, table=True):
    """Anonymer Testdurchlauf. score wird erst beim Abschluss gesetzt."""

    id: int | None = Field(default=None, primary_key=True)
    test_id: int = Field(foreign_key="test.id", index=True)
    started_at: datetime = Field(default_factory=utcnow)
    submitted_at: datetime | None = None
    score: int | None = None


class Answer(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    attempt_id: int = Field(foreign_key="attempt.id", index=True)
    item_id: int = Field(foreign_key="item.id")
    selected_option: int
