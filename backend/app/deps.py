from fastapi import Depends
from sqlalchemy.orm import Session

from .db import get_db
from .models import User


def get_current_user(db: Session = Depends(get_db)) -> User:
    """DEV STUB — Google OAuth 세션 도입 전까지 고정 개발 유저.
    TODO: 세션 쿠키 인증으로 교체 (docs/data_model.md §인증)."""
    u = db.query(User).filter_by(auth_provider="dev", provider_sub="dev").first()
    if u is None:
        u = User(auth_provider="dev", provider_sub="dev", email="dev@local", level_band=1)
        db.add(u)
        db.commit()
        db.refresh(u)
    return u
