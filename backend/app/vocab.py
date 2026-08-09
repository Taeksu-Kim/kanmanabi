"""단어장 API (B6) — 등급별 목록·검색·상세·즐겨찾기.

학습 상태는 별도 컬럼이 아니라 **해당 단어에 연결된 문제의 ReviewCard에서 파생**한다
(어휘 자체는 SRS 대상이 아니고 문제 단위로 돈다). 계약: docs/api_contract.md §3.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import cast, func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.types import Text

from . import models
from .db import get_db
from .deps import get_current_user

router = APIRouter(prefix="/api/vocab")

MAX_LIMIT = 100


def _status_map(db: Session, user_id: int, vocab_ids: list[int]) -> dict[int, str]:
    """vocab_id → not_started | learning | reviewing.
    해당 단어의 문제 중 카드가 하나도 없으면 not_started, reps<2면 learning, 그 외 reviewing."""
    if not vocab_ids:
        return {}
    rows = (db.query(models.Question.vocab_id, func.max(models.ReviewCard.reps))
            .join(models.ReviewCard,
                  (models.ReviewCard.item_id == models.Question.id)
                  & (models.ReviewCard.item_type == "question")
                  & (models.ReviewCard.user_id == user_id))
            .filter(models.Question.vocab_id.in_(vocab_ids))
            .group_by(models.Question.vocab_id).all())
    seen = {vid: ("learning" if (reps or 0) < 2 else "reviewing") for vid, reps in rows}
    return {vid: seen.get(vid, "not_started") for vid in vocab_ids}


def _serialize(v: models.Vocab, status: str, favorite: bool):
    return {"id": v.id, "word": v.word, "pos": v.pos, "level_band": v.level_band,
            "ja": v.ja, "hanja": v.hanja, "guide": v.guide,
            "status": status, "favorite": favorite}


@router.get("")
def list_vocab(level: int | None = Query(default=None, ge=1, le=6),
               q: str | None = None,
               favorite: bool = False,
               cursor: int = 0,
               limit: int = Query(default=50, ge=1, le=MAX_LIMIT),
               db: Session = Depends(get_db), user=Depends(get_current_user)):
    """커서 페이지네이션 — `cursor`는 직전 페이지 마지막 id. 응답의 next_cursor를 그대로 넘긴다."""
    qq = db.query(models.Vocab).filter(models.Vocab.id > cursor)
    if level is not None:
        qq = qq.filter(models.Vocab.level_band == level)
    if q:
        like = f"%{q}%"
        # ja는 JSON 배열 — 텍스트로 캐스팅해 부분일치(일본어 뜻으로도 찾을 수 있어야 한다)
        qq = qq.filter(or_(models.Vocab.word.like(like),
                           models.Vocab.hanja.like(like),
                           cast(models.Vocab.ja, Text).like(like)))
    if favorite:
        fav = select(models.VocabFavorite.vocab_id).where(
            models.VocabFavorite.user_id == user.id)
        qq = qq.filter(models.Vocab.id.in_(fav))

    items = qq.order_by(models.Vocab.id).limit(limit + 1).all()
    has_more = len(items) > limit
    items = items[:limit]

    ids = [v.id for v in items]
    status = _status_map(db, user.id, ids)
    favs = {f.vocab_id for f in db.query(models.VocabFavorite)
            .filter(models.VocabFavorite.user_id == user.id,
                    models.VocabFavorite.vocab_id.in_(ids)).all()} if ids else set()

    return {"items": [_serialize(v, status[v.id], v.id in favs) for v in items],
            "next_cursor": items[-1].id if (items and has_more) else None}


@router.get("/{vocab_id}")
def get_vocab(vocab_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    v = db.get(models.Vocab, vocab_id)
    if v is None:
        raise HTTPException(404, "vocab not found")
    fav = db.get(models.VocabFavorite, {"user_id": user.id, "vocab_id": vocab_id}) is not None
    return _serialize(v, _status_map(db, user.id, [vocab_id])[vocab_id], fav)


@router.put("/{vocab_id}/favorite")
def add_favorite(vocab_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if db.get(models.Vocab, vocab_id) is None:
        raise HTTPException(404, "vocab not found")
    if db.get(models.VocabFavorite, {"user_id": user.id, "vocab_id": vocab_id}) is None:
        db.add(models.VocabFavorite(user_id=user.id, vocab_id=vocab_id))
        db.commit()
    return {"vocab_id": vocab_id, "favorite": True}


@router.delete("/{vocab_id}/favorite")
def remove_favorite(vocab_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    row = db.get(models.VocabFavorite, {"user_id": user.id, "vocab_id": vocab_id})
    if row:
        db.delete(row)
        db.commit()
    return {"vocab_id": vocab_id, "favorite": False}
