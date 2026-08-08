"""학습 루프 API — reps 엔진 코어.

next(출제: due 복습 우선 → 신규) / answer(채점+SRS 갱신) / due(오늘 복습 수).
현재 어휘문제(vocab 연결)만 대상. 유저는 개발 스텁(deps.get_current_user).
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models
from .db import get_db
from .deps import get_current_user
from .srs import schedule

router = APIRouter(prefix="/api/study")


def _serialize(q: models.Question):
    # 정답은 클라이언트에 노출하지 않는다.
    return {"id": q.id, "qtype": q.qtype, "prompt": q.prompt,
            "choices": q.choices, "difficulty": q.difficulty}


@router.get("/next")
def next_item(level: int = 1, db: Session = Depends(get_db), user=Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    # 1) due 복습 카드 우선
    card = (db.query(models.ReviewCard)
            .filter(models.ReviewCard.user_id == user.id,
                    models.ReviewCard.item_type == "question",
                    models.ReviewCard.due_at <= now)
            .order_by(models.ReviewCard.due_at).first())
    if card:
        q = db.get(models.Question, card.item_id)
        if q:
            return {"mode": "review", "question": _serialize(q)}
    # 2) 신규: 해당 등급(vocab 경유) 중 아직 카드 없는 문제
    carded = select(models.ReviewCard.item_id).where(
        models.ReviewCard.user_id == user.id,
        models.ReviewCard.item_type == "question")
    q = (db.query(models.Question)
         .join(models.Vocab, models.Question.vocab_id == models.Vocab.id)
         .filter(models.Vocab.level_band <= level, ~models.Question.id.in_(carded))
         .order_by(func.random()).first())
    if q is None:
        return {"mode": "done", "question": None}
    return {"mode": "new", "question": _serialize(q)}


class AnswerIn(BaseModel):
    question_id: int
    answer: str = ""


@router.post("/answer")
def answer(payload: AnswerIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.get(models.Question, payload.question_id)
    if q is None:
        raise HTTPException(404, "question not found")
    given = payload.answer.strip()
    correct = given == (q.answer or "").strip()   # MVP: 정확일치 (동의어 세트는 Phase 1)

    db.add(models.Attempt(user_id=user.id, item_type="question", item_id=q.id,
                          is_correct=correct, user_answer=given))
    card = (db.query(models.ReviewCard)
            .filter_by(user_id=user.id, item_type="question", item_id=q.id).first())
    if card is None:
        card = models.ReviewCard(user_id=user.id, item_type="question", item_id=q.id,
                                 ease=2.5, interval_days=0, reps=0, lapses=0)
        db.add(card)
    schedule(card, correct)
    db.commit()
    return {"correct": correct, "correct_answer": q.answer,
            "explanation": q.explanation, "next_due": card.due_at.isoformat()}


@router.get("/due")
def due(db: Session = Depends(get_db), user=Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    n = (db.query(func.count()).select_from(models.ReviewCard)
         .filter(models.ReviewCard.user_id == user.id,
                 models.ReviewCard.item_type == "question",
                 models.ReviewCard.due_at <= now).scalar())
    return {"due_count": n}
