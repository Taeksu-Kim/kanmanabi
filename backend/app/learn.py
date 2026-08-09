"""프로필(/api/me)과 학습 허브 요약(/api/learn/summary).

허브는 프론트 `/learn` 한 화면을 한 번의 호출로 채우기 위한 집계 엔드포인트다.
계약: docs/api_contract.md §3. 필드는 기존 API와 맞춰 snake_case.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models
from .db import get_db
from .deps import get_current_user
from .study import _due_count

router = APIRouter(prefix="/api")

PREVIEW_LIMIT = 3


def _ep_index(ep_no: str) -> int:
    """'EP07' → 7. order_index가 있지만 프론트는 EP 번호로 표시한다."""
    return int(ep_no[2:])


@router.get("/me")
def me(db: Session = Depends(get_db), user=Depends(get_current_user)):
    # nickname 컬럼은 두지 않는다(B9) — 표시 이름은 name 하나로 통일.
    return {"id": user.id, "name": user.name, "email": user.email,
            "picture": user.picture, "level_band": user.level_band}


class MeUpdate(BaseModel):
    level_band: int | None = Field(default=None, ge=1, le=6)
    name: str | None = None


@router.patch("/me")
def update_me(payload: MeUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if payload.level_band is not None:
        user.level_band = payload.level_band
    if payload.name is not None:
        user.name = payload.name
    db.commit()
    db.refresh(user)
    return me(db, user)


def _resume_episode(episodes, rows, done) -> int | None:
    """이어하기 위치 — 마지막으로 연 EP 기준(C0012).

    기록 없음 → None / 그 EP가 미완료 → 그 EP / 완료면 다음 순서 EP(마지막이면 마지막).
    `current_episode`("첫 미완료 EP")와는 다른 값이다: 완료한 EP를 다시 열어봐도
    이어하기는 그다음을 가리키고, current는 여전히 앞쪽 미완료 EP를 가리킨다.
    """
    opened = [r for r in rows if r.last_opened_at is not None]
    if not opened:
        return None
    last = max(opened, key=lambda r: r.last_opened_at)
    order = [e.id for e in episodes]
    if last.episode_id not in order:
        return None
    idx = order.index(last.episode_id)
    if last.episode_id in done and idx + 1 < len(episodes):
        idx += 1                                  # 완료했으면 다음 EP로
    return _ep_index(episodes[idx].ep_no)


@router.get("/learn/summary")
def learn_summary(db: Session = Depends(get_db), user=Depends(get_current_user)):
    level = user.level_band or 1

    preview = (db.query(models.Vocab)
               .filter(models.Vocab.level_band == level)
               .order_by(models.Vocab.id).limit(PREVIEW_LIMIT).all())

    episodes = db.query(models.Episode).order_by(models.Episode.order_index).all()
    rows = db.query(models.UserEpisodeProgress).filter_by(user_id=user.id).all()
    done = {p.episode_id for p in rows if _derive_status(p) == "completed"}
    completed = sorted(_ep_index(e.ep_no) for e in episodes if e.id in done)
    # 현재 EP = 아직 완료되지 않은 첫 EP (전부 끝냈으면 마지막)
    remaining = [e for e in episodes if e.id not in done]
    current = _ep_index(remaining[0].ep_no) if remaining else (
        _ep_index(episodes[-1].ep_no) if episodes else 0)

    return {
        "level_band": level,
        "vocabulary": {
            "preview": [{"id": v.id, "word": v.word,
                         "meaning_ja": v.ja[0] if v.ja else None} for v in preview],
            "due_count": _due_count(db, user.id, "vocabulary"),
        },
        "grammar": {
            "current_episode": current,
            "resume_episode": _resume_episode(episodes, rows, done),
            "total_episodes": len(episodes),
            "completed_episodes": completed,
            "due_count": _due_count(db, user.id, "grammar"),
        },
    }


STEPS = ("video", "point", "practice")       # B8 (C0005 확정)


def _derive_status(row: models.UserEpisodeProgress) -> str:
    """status는 저장값이 아니라 세 단계에서 파생한다 — 두 값이 어긋날 수 없게."""
    flags = [row.video_done, row.point_done, row.practice_done]
    if all(flags):
        return "completed"
    return "in_progress" if any(flags) else "not_started"


def _progress_payload(ep: models.Episode, row: models.UserEpisodeProgress | None):
    steps = {s: bool(row and getattr(row, f"{s}_done")) for s in STEPS}
    return {"ep_no": ep.ep_no, "steps": steps,
            "status": _derive_status(row) if row else "not_started"}


@router.get("/episodes")
def episodes(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """EP 목록 + 단계별 진도(B8). status는 세 단계에서 파생된 값이다."""
    eps = db.query(models.Episode).order_by(models.Episode.order_index).all()
    rows = {p.episode_id: p for p in db.query(models.UserEpisodeProgress)
            .filter_by(user_id=user.id).all()}
    return [{"ep_no": e.ep_no, "title": e.title, "order_index": e.order_index,
             "youtube_id": e.youtube_id, "summary": e.summary,
             **_progress_payload(e, rows.get(e.id))} for e in eps]


class ProgressIn(BaseModel):
    """보낸 단계만 갱신한다(부분 업데이트). 셋 다 true면 status가 completed로 파생된다.

    `opened`는 단계값을 건드리지 않고 방문 기록(last_opened_at)만 남긴다 —
    EP 상세를 열기만 해도 이어하기 위치로 기억하기 위함.
    """
    video: bool | None = None
    point: bool | None = None
    practice: bool | None = None
    opened: bool | None = None


@router.put("/episodes/{ep_no}/progress")
def set_progress(ep_no: str, payload: ProgressIn,
                 db: Session = Depends(get_db), user=Depends(get_current_user)):
    ep = db.query(models.Episode).filter_by(ep_no=ep_no).first()
    if ep is None:
        raise HTTPException(404, f"episode {ep_no} not found")
    row = (db.query(models.UserEpisodeProgress)
           .filter_by(user_id=user.id, episode_id=ep.id).first())
    if row is None:
        row = models.UserEpisodeProgress(user_id=user.id, episode_id=ep.id)
        db.add(row)
    touched = False
    for step in STEPS:
        val = getattr(payload, step)
        if val is not None:
            setattr(row, f"{step}_done", val)
            touched = True

    if touched or payload.opened:          # 단계 갱신도 '방문'으로 친다
        row.last_opened_at = func.now()

    row.status = _derive_status(row)
    row.completed_at = func.now() if row.status == "completed" else None
    db.commit()
    db.refresh(row)
    return _progress_payload(ep, row)
