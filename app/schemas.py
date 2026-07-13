from datetime import datetime

from pydantic import BaseModel, Field


class TestCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)


class ItemCreate(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    options: list[str] = Field(min_length=2, max_length=10)
    correct_option: int = Field(ge=0)


class ItemRead(BaseModel):
    id: int
    position: int
    question: str
    options: list[str]
    correct_option: int


class TestRead(BaseModel):
    id: int
    title: str
    description: str
    access_code: str
    created_at: datetime
    items: list[ItemRead]


class TestSummary(BaseModel):
    id: int
    title: str
    access_code: str
    created_at: datetime
    item_count: int


# ItemPublic ist die Sicht für Teilnehmer:innen und enthält bewusst
# kein correct_option -- die Lösung darf den Server nicht verlassen.
class ItemPublic(BaseModel):
    id: int
    position: int
    question: str
    options: list[str]


class AttemptStart(BaseModel):
    access_code: str = Field(min_length=1, max_length=50)


class AnswerSave(BaseModel):
    item_id: int
    selected_option: int = Field(ge=0)


class AnswerRead(BaseModel):
    item_id: int
    selected_option: int


class AttemptRead(BaseModel):
    id: int
    test_id: int
    test_title: str
    started_at: datetime
    submitted_at: datetime | None
    items: list[ItemPublic]
    answers: list[AnswerRead]


class AttemptResult(BaseModel):
    id: int
    submitted_at: datetime
    score: int
    max_score: int


class ResultEntry(BaseModel):
    attempt_id: int
    started_at: datetime
    submitted_at: datetime | None
    score: int | None
    max_score: int


class TestResults(BaseModel):
    test_id: int
    test_title: str
    max_score: int
    attempts: list[ResultEntry]
    submitted_count: int
    average_score: float | None
    score_distribution: dict[int, int]
