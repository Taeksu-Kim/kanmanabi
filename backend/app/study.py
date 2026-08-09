"""학습 루프 API — reps 엔진 코어.

next(출제: due 복습 우선 → 신규) / answer(채점+SRS 갱신) / due(오늘 복습 수).
현재 어휘문제(vocab 연결)만 대상. 유저는 개발 스텁(deps.get_current_user).
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from . import models
from .db import get_db
from .deps import get_current_user
from .srs import schedule

router = APIRouter(prefix="/api/study")


def _norm(s: str) -> str:
    """채점용 정규화 — 앞뒤 공백 + 내부 연속공백. 정답에 공백이 든 문항이 많다
    (안 앉아요·찾아봐 주세요·ㄴ 후에). 동의어 세트는 Phase 1."""
    return " ".join((s or "").split())


def _serialize(q: models.Question):
    # 정답은 클라이언트에 노출하지 않는다.
    # track: 어휘(vocab_id)냐 문법(episode_id)이냐 — 프론트가 트랙을 나눠 표시한다.
    return {"id": q.id, "qtype": q.qtype, "prompt": q.prompt,
            "choices": q.choices, "difficulty": q.difficulty,
            "track": "grammar" if q.episode_id else "vocabulary",
            "ep_no": q.episode.ep_no if q.episode_id else None}


def _track_filter(track: str | None):
    """트랙 = episode_id 유무. 문법문항도 vocab_id를 가질 수 있어(조사·활용) 이쪽이 기준."""
    if track == "grammar":
        return models.Question.episode_id.isnot(None)
    if track == "vocabulary":
        return models.Question.episode_id.is_(None)
    return None


@router.get("/next")
def next_item(level: int = 1, track: str | None = None, ep_no: str | None = None,
              db: Session = Depends(get_db), user=Depends(get_current_user)):
    if track not in (None, "grammar", "vocabulary"):
        raise HTTPException(422, "track must be 'grammar' or 'vocabulary'")
    now = datetime.now(timezone.utc)
    tf = _track_filter(track)
    if ep_no:                                   # EP별 문법 세션 (EP 상세 화면의 연습)
        ep = db.query(models.Episode).filter_by(ep_no=ep_no).first()
        if ep is None:
            raise HTTPException(404, f"episode {ep_no} not found")
        ep_f = models.Question.episode_id == ep.id
        tf = ep_f if tf is None else tf & ep_f

    # 1) due 복습 카드 우선 (트랙 지정 시 그 트랙의 카드만)
    cq = (db.query(models.ReviewCard)
          .filter(models.ReviewCard.user_id == user.id,
                  models.ReviewCard.item_type == "question",
                  models.ReviewCard.due_at <= now))
    if tf is not None:
        cq = cq.join(models.Question, models.ReviewCard.item_id == models.Question.id).filter(tf)
    card = cq.order_by(models.ReviewCard.due_at).first()
    if card:
        q = db.get(models.Question, card.item_id)
        if q:
            return {"mode": "review", "question": _serialize(q)}

    # 2) 신규: 아직 카드 없는 문제. 문법문항은 vocab_id가 없을 수 있어 outerjoin —
    #    inner join이면 뉘앙스·EP03·EP07(351문항)이 영원히 출제되지 않는다.
    carded = select(models.ReviewCard.item_id).where(
        models.ReviewCard.user_id == user.id,
        models.ReviewCard.item_type == "question")
    qq = (db.query(models.Question)
          .outerjoin(models.Vocab, models.Question.vocab_id == models.Vocab.id)
          .filter(~models.Question.id.in_(carded),
                  models.Question.needs_review.is_(False),   # 검토 전 문제 서빙 제외
                  # 등급 제한은 vocab 연결 문항에만 적용 가능(questions에 level 컬럼이 없다).
                  # EP 문항은 전부 초급이라 통과시킨다.
                  or_(models.Vocab.level_band <= level, models.Question.vocab_id.is_(None))))
    if tf is not None:
        qq = qq.filter(tf)
    q = qq.order_by(func.random()).first()
    if q is None:
        return {"mode": "done", "question": None}
    return {"mode": "new", "question": _serialize(q)}


class AnswerIn(BaseModel):
    question_id: int
    answer: str = ""
    # 해당 문항에서 선택지를 한 번이라도 열었는지. 미전송이면 None(모름)으로 기록한다.
    used_choices: bool | None = None


@router.post("/answer")
def answer(payload: AnswerIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.get(models.Question, payload.question_id)
    if q is None:
        raise HTTPException(404, "question not found")
    given = payload.answer.strip()
    correct = _norm(given) == _norm(q.answer)     # MVP: 공백 정규화 후 정확일치

    db.add(models.Attempt(user_id=user.id, item_type="question", item_id=q.id,
                          is_correct=correct, user_answer=given,
                          used_choices=payload.used_choices))
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


def _due_count(db: Session, user_id: int, track: str | None = None) -> int:
    now = datetime.now(timezone.utc)
    q = (db.query(func.count()).select_from(models.ReviewCard)
         .filter(models.ReviewCard.user_id == user_id,
                 models.ReviewCard.item_type == "question",
                 models.ReviewCard.due_at <= now))
    tf = _track_filter(track)
    if tf is not None:
        q = q.join(models.Question, models.ReviewCard.item_id == models.Question.id).filter(tf)
    return q.scalar()


@router.get("/due")
def due(track: str | None = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """track 생략 시 전체(기존 동작). 트랙별 카운트가 필요하면 ?track= 로 좁힌다."""
    if track not in (None, "grammar", "vocabulary"):
        raise HTTPException(422, "track must be 'grammar' or 'vocabulary'")
    return {"due_count": _due_count(db, user.id, track)}
