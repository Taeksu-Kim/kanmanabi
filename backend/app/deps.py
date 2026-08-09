from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .auth import COOKIE_NAME, read_session
from .config import settings
from .db import get_db
from .models import User


def _dev_user(db: Session) -> User:
    """개발 스텁 — GOOGLE_CLIENT_ID가 없을 때만 쓴다. 고정 유저 1명."""
    u = db.query(User).filter_by(auth_provider="dev", provider_sub="dev").first()
    if u is None:
        u = User(auth_provider="dev", provider_sub="dev", email="dev@local", level_band=1)
        db.add(u)
        db.commit()
        db.refresh(u)
    return u


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """세션 쿠키 → 유저. `AUTH_REQUIRED=false`(개발)면 dev 스텁으로 폴백.

    폴백 여부는 client_id 유무가 아니라 AUTH_REQUIRED로 결정한다 — 로컬에서 client_id를
    넣고 로그인을 붙이는 동안에도 나머지 화면이 막히지 않게 하기 위함.
    운영은 AUTH_REQUIRED=true로 두어 폴백이 새어나가지 않도록 한다.
    """
    uid = read_session(request.cookies.get(COOKIE_NAME))
    if uid is not None:
        user = db.get(User, uid)
        if user is not None:
            return user
    if not settings.auth_required:
        return _dev_user(db)
    raise HTTPException(401, "not authenticated")
