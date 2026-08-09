"""Standalone three-form conjugation drill backed by the existing attempt/SRS tables."""
from datetime import datetime, timezone
from random import choice

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models
from .conjugation_logic import forms, rule_for
from .db import get_db
from .deps import get_current_user
from .srs import schedule

router = APIRouter(prefix="/api/conjugation")
FORM_TYPES = {"stem": "conj_stem", "ae": "conj_ae", "eu": "conj_eu"}


def _serialize(vocab):
    rule = rule_for(vocab.word)
    return {
        "id": vocab.id,
        "word": vocab.word,
        "meaning_ja": vocab.ja[0] if vocab.ja else None,
        "rule": {"id": rule["id"], "label_ja": rule["label_ja"]},
    }


def _valid_candidates(db, level):
    candidates = (db.query(models.Vocab)
                  .filter(models.Vocab.level_band <= level,
                          models.Vocab.pos.in_(("동사", "형용사")))
                  .order_by(func.random()).limit(300).all())
    return [vocab for vocab in candidates if forms(vocab.word)]


@router.get("/next")
def next_drill(level: int = 1, db: Session = Depends(get_db), user=Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    due = (db.query(models.ReviewCard)
           .filter(models.ReviewCard.user_id == user.id,
                   models.ReviewCard.item_type.in_(tuple(FORM_TYPES.values())),
                   models.ReviewCard.due_at <= now)
           .order_by(models.ReviewCard.due_at).first())
    if due:
        vocab = db.get(models.Vocab, due.item_id)
        if vocab and forms(vocab.word):
            return {"mode": "review", "drill": _serialize(vocab)}

    carded_ids = (db.query(models.ReviewCard.item_id)
                  .filter(models.ReviewCard.user_id == user.id,
                          models.ReviewCard.item_type.in_(tuple(FORM_TYPES.values()))))
    candidates = [v for v in _valid_candidates(db, level) if v.id not in {row[0] for row in carded_ids.all()}]
    if not candidates:
        candidates = _valid_candidates(db, level)
    if not candidates:
        return {"mode": "done", "drill": None}
    return {"mode": "new", "drill": _serialize(choice(candidates))}


class AnswerIn(BaseModel):
    vocab_id: int
    stem: str = ""
    ae: str = ""
    eu: str = ""


@router.post("/answer")
def answer_drill(payload: AnswerIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    vocab = db.get(models.Vocab, payload.vocab_id)
    expected = forms(vocab.word) if vocab else None
    if not vocab or not expected:
        raise HTTPException(404, "conjugation drill not found")

    results = {}
    any_wrong = False
    for key, item_type in FORM_TYPES.items():
        given = getattr(payload, key).strip()
        correct = given == expected[key]
        any_wrong = any_wrong or not correct
        results[key] = {"correct": correct, "given": given, "answer": expected[key]}
        db.add(models.Attempt(user_id=user.id, item_type=item_type, item_id=vocab.id,
                              is_correct=correct, user_answer=given, used_choices=False))
        card = (db.query(models.ReviewCard)
                .filter_by(user_id=user.id, item_type=item_type, item_id=vocab.id).first())
        if card is None:
            card = models.ReviewCard(user_id=user.id, item_type=item_type, item_id=vocab.id,
                                     ease=2.5, interval_days=0, reps=0, lapses=0)
            db.add(card)
        schedule(card, correct)

    rule = rule_for(vocab.word)
    db.commit()
    return {
        "results": results,
        "rule": rule,
        "contrast": f"{expected['stem']}고 / {expected['ae']}요 / {expected['eu']}면",
        "added_to_review": any_wrong,
    }


@router.get("/summary")
def summary(db: Session = Depends(get_db), user=Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    due_count = (db.query(func.count()).select_from(models.ReviewCard)
                 .filter(models.ReviewCard.user_id == user.id,
                         models.ReviewCard.item_type.in_(tuple(FORM_TYPES.values())),
                         models.ReviewCard.due_at <= now).scalar())
    wrong_attempts = (db.query(models.Attempt)
                      .filter(models.Attempt.user_id == user.id,
                              models.Attempt.item_type.in_(tuple(FORM_TYPES.values())),
                              models.Attempt.is_correct.is_(False)).all())
    counts = {}
    for attempt in wrong_attempts:
        vocab = db.get(models.Vocab, attempt.item_id)
        if vocab:
            rule = rule_for(vocab.word)
            counts[rule["label_ja"]] = counts.get(rule["label_ja"], 0) + 1
    weakest_rule = max(counts, key=counts.get) if counts else None
    return {"due_count": due_count, "weakest_rule": weakest_rule}
