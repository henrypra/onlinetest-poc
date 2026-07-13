import logging
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Attempt, Item, Test
from app.schemas import (
    ItemCreate,
    ItemRead,
    ResultEntry,
    TestCreate,
    TestRead,
    TestResults,
    TestSummary,
)

logger = logging.getLogger("onlinetest")

router = APIRouter(prefix="/api/tests", tags=["tests"])

# ohne 0/O/1/I/L, die werden beim Abtippen gern verwechselt
_CODE_ALPHABET = "".join(
    c for c in string.ascii_uppercase + string.digits if c not in "0O1IL"
)


def _generate_access_code(session: Session, length: int = 8) -> str:
    while True:
        code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))
        if not session.exec(select(Test).where(Test.access_code == code)).first():
            return code


def _get_test_or_404(session: Session, test_id: int) -> Test:
    test = session.get(Test, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test nicht gefunden")
    return test


def _test_to_read(session: Session, test: Test) -> TestRead:
    items = session.exec(
        select(Item).where(Item.test_id == test.id).order_by(Item.position)
    ).all()
    return TestRead(
        id=test.id,
        title=test.title,
        description=test.description,
        access_code=test.access_code,
        created_at=test.created_at,
        items=[ItemRead.model_validate(i, from_attributes=True) for i in items],
    )


@router.get("", response_model=list[TestSummary])
def list_tests(session: Session = Depends(get_session)):
    """Alle Tests (Admin-Sicht)."""
    tests = session.exec(select(Test).order_by(Test.created_at.desc())).all()
    return [
        TestSummary(
            id=t.id,
            title=t.title,
            access_code=t.access_code,
            created_at=t.created_at,
            item_count=len(
                session.exec(select(Item).where(Item.test_id == t.id)).all()
            ),
        )
        for t in tests
    ]


@router.post("", response_model=TestRead, status_code=201)
def create_test(data: TestCreate, session: Session = Depends(get_session)):
    """Neuen Test anlegen, Zugangscode wird generiert."""
    test = Test(
        title=data.title,
        description=data.description,
        access_code=_generate_access_code(session),
    )
    session.add(test)
    session.commit()
    session.refresh(test)
    logger.info("Test angelegt: id=%s, code=%s", test.id, test.access_code)
    return _test_to_read(session, test)


@router.get("/{test_id}", response_model=TestRead)
def get_test(test_id: int, session: Session = Depends(get_session)):
    """Test inklusive aller Fragen (Admin-Sicht)."""
    return _test_to_read(session, _get_test_or_404(session, test_id))


@router.post("/{test_id}/items", response_model=ItemRead, status_code=201)
def add_item(
    test_id: int, data: ItemCreate, session: Session = Depends(get_session)
):
    """Multiple-Choice-Frage zu einem Test hinzufügen."""
    test = _get_test_or_404(session, test_id)

    if data.correct_option >= len(data.options):
        raise HTTPException(
            status_code=422,
            detail="correct_option verweist auf keine vorhandene Antwortoption",
        )

    existing = session.exec(select(Item).where(Item.test_id == test.id)).all()
    item = Item(
        test_id=test.id,
        position=len(existing) + 1,
        question=data.question,
        options=data.options,
        correct_option=data.correct_option,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return ItemRead.model_validate(item, from_attributes=True)


@router.get("/{test_id}/results", response_model=TestResults)
def get_results(test_id: int, session: Session = Depends(get_session)):
    """Ergebnisse eines Tests, Teilnehmer:innen nur als anonyme IDs."""
    test = _get_test_or_404(session, test_id)
    max_score = len(session.exec(select(Item).where(Item.test_id == test.id)).all())
    attempts = session.exec(
        select(Attempt).where(Attempt.test_id == test.id).order_by(Attempt.started_at)
    ).all()

    submitted = [a.score for a in attempts if a.submitted_at is not None]
    distribution: dict[int, int] = {}
    for score in submitted:
        distribution[score] = distribution.get(score, 0) + 1

    return TestResults(
        test_id=test.id,
        test_title=test.title,
        max_score=max_score,
        attempts=[
            ResultEntry(
                attempt_id=a.id,
                started_at=a.started_at,
                submitted_at=a.submitted_at,
                score=a.score,
                max_score=max_score,
            )
            for a in attempts
        ],
        submitted_count=len(submitted),
        average_score=round(sum(submitted) / len(submitted), 2) if submitted else None,
        score_distribution=distribution,
    )
