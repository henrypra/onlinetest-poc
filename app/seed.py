"""Beispieltest mit festem Zugangscode, wird beim ersten Start angelegt.
DEMO_ACCESS_CODE="" schaltet das ab."""

import logging
import os

from sqlmodel import Session, select

from app.models import Item, Test

logger = logging.getLogger("onlinetest")

DEMO_ACCESS_CODE = os.environ.get("DEMO_ACCESS_CODE", "ZFH2VVKZ")

_DEMO_ITEMS = [
    {
        "question": "Ein Fahrrad kostet 240 €. Der Preis wird um 25 % gesenkt. "
                    "Wie viel kostet das Fahrrad jetzt?",
        "options": ["60 €", "180 €", "215 €", "300 €"],
        "correct_option": 1,
    },
    {
        "question": "Welcher Bruch ist am größten?",
        "options": ["1/3", "2/5", "3/8", "1/2"],
        "correct_option": 3,
    },
    {
        "question": "„Die Ferien beginnen nächste Woche, __ freuen sich alle "
                    "Schülerinnen und Schüler.“ – Welches Wort passt in die Lücke?",
        "options": ["deshalb", "obwohl", "trotzdem nicht", "damit"],
        "correct_option": 0,
    },
    {
        "question": "Setze die Zahlenfolge fort: 2, 4, 8, 16, …",
        "options": ["18", "24", "32", "64"],
        "correct_option": 2,
    },
    {
        "question": "Ein Diagramm zeigt die Lesestunden einer Klasse pro Woche: "
                    "Mo 3, Di 5, Mi 2, Do 5, Fr 5. Welcher Wert ist der Median?",
        "options": ["2", "3", "4", "5"],
        "correct_option": 3,
    },
]


def seed_demo_data(session: Session) -> None:
    if not DEMO_ACCESS_CODE:
        return
    if session.exec(select(Test).where(Test.access_code == DEMO_ACCESS_CODE)).first():
        return

    test = Test(
        title="Demo: Kompetenztest Klasse 7 (Mathematik & Lesen)",
        description=(
            "Beispieltest zur Kompetenzerfassung – fünf Multiple-Choice-Aufgaben "
            "aus den Bereichen Mathematik, Sprache und logisches Denken."
        ),
        access_code=DEMO_ACCESS_CODE,
    )
    session.add(test)
    session.commit()
    session.refresh(test)

    for position, data in enumerate(_DEMO_ITEMS, start=1):
        session.add(Item(test_id=test.id, position=position, **data))
    session.commit()
    logger.info("Demo-Test angelegt: id=%s, code=%s", test.id, DEMO_ACCESS_CODE)
