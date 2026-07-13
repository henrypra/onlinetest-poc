import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Answer, Attempt, Item, Test, utcnow
from app.schemas import (
    AnswerRead,
    AnswerSave,
    AttemptRead,
    AttemptResult,
    AttemptStart,
    ItemPublic,
)

logger = logging.getLogger("onlinetest")

router = APIRouter(prefix="/api/attempts", tags=["attempts"])


def _get_attempt_or_404(session: Session, attempt_id: int) -> Attempt:
    attempt = session.get(Attempt, attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Durchlauf nicht gefunden")
    return attempt


def _attempt_to_read(session: Session, attempt: Attempt) -> AttemptRead:
    test = session.get(Test, attempt.test_id)
    items = session.exec(
        select(Item).where(Item.test_id == attempt.test_id).order_by(Item.position)
    ).all()
    answers = session.exec(
        select(Answer).where(Answer.attempt_id == attempt.id)
    ).all()
    return AttemptRead(
        id=attempt.id,
        test_id=attempt.test_id,
        test_title=test.title,
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
        items=[ItemPublic.model_validate(i, from_attributes=True) for i in items],
        answers=[AnswerRead.model_validate(a, from_attributes=True) for a in answers],
    )


@router.post("", response_model=AttemptRead, status_code=201)
def start_attempt(data: AttemptStart, session: Session = Depends(get_session)):
    """Testdurchlauf per Zugangscode starten. Fragen kommen ohne Lösungen zurück."""
    code = data.access_code.strip().upper()
    test = session.exec(select(Test).where(Test.access_code == code)).first()
    if not test:
        logger.warning("Ungültiger Zugangscode: %s", code)
        raise HTTPException(status_code=404, detail="Ungültiger Zugangscode")

    attempt = Attempt(test_id=test.id)
    session.add(attempt)
    session.commit()
    session.refresh(attempt)
    logger.info("Durchlauf gestartet: attempt_id=%s, test_id=%s", attempt.id, test.id)
    return _attempt_to_read(session, attempt)


@router.get("/{attempt_id}", response_model=AttemptRead)
def get_attempt(attempt_id: int, session: Session = Depends(get_session)):
    """Durchlauf inkl. bisheriger Antworten, z. B. für den Wiedereinstieg."""
    return _attempt_to_read(session, _get_attempt_or_404(session, attempt_id))


@router.patch("/{attempt_id}/answers", response_model=AnswerRead)
def save_answer(
    attempt_id: int, data: AnswerSave, session: Session = Depends(get_session)
):
    """Einzelne Antwort speichern bzw. überschreiben (Zwischenspeicherung)."""
    attempt = _get_attempt_or_404(session, attempt_id)
    if attempt.submitted_at is not None:
        raise HTTPException(status_code=409, detail="Durchlauf ist bereits abgeschlossen")

    item = session.get(Item, data.item_id)
    if not item or item.test_id != attempt.test_id:
        raise HTTPException(status_code=404, detail="Frage gehört nicht zu diesem Test")
    if data.selected_option >= len(item.options):
        raise HTTPException(
            status_code=422,
            detail="selected_option verweist auf keine vorhandene Antwortoption",
        )

    answer = session.exec(
        select(Answer)
        .where(Answer.attempt_id == attempt.id)
        .where(Answer.item_id == item.id)
    ).first()
    if answer:
        answer.selected_option = data.selected_option
    else:
        answer = Answer(
            attempt_id=attempt.id,
            item_id=item.id,
            selected_option=data.selected_option,
        )
    session.add(answer)
    session.commit()
    session.refresh(answer)
    return AnswerRead.model_validate(answer, from_attributes=True)


@router.post("/{attempt_id}/submit", response_model=AttemptResult)
def submit_attempt(attempt_id: int, session: Session = Depends(get_session)):
    """Durchlauf abschließen; der Score wird serverseitig berechnet."""
    attempt = _get_attempt_or_404(session, attempt_id)
    if attempt.submitted_at is not None:
        raise HTTPException(status_code=409, detail="Durchlauf ist bereits abgeschlossen")

    items = session.exec(select(Item).where(Item.test_id == attempt.test_id)).all()
    answers = session.exec(
        select(Answer).where(Answer.attempt_id == attempt.id)
    ).all()
    answered = {a.item_id: a.selected_option for a in answers}

    attempt.score = sum(
        1 for item in items if answered.get(item.id) == item.correct_option
    )
    attempt.submitted_at = utcnow()
    session.add(attempt)
    session.commit()
    logger.info(
        "Durchlauf abgeschlossen: attempt_id=%s, score=%s/%s",
        attempt.id, attempt.score, len(items),
    )
    return AttemptResult(
        id=attempt.id,
        submitted_at=attempt.submitted_at,
        score=attempt.score,
        max_score=len(items),
    )
