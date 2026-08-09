"""Google 로그인과 세션 쿠키. 설계: docs/data_model.md §인증.

흐름: 프론트가 Google Identity Services로 ID 토큰 획득 → `POST /api/auth/google` →
백엔드가 검증(aud=우리 client_id) → provider_sub 기준 유저 upsert → **httpOnly 세션 쿠키** 발급.
세션은 서명 토큰이라 sessions 테이블이 없다.

설정 두 개가 독립이다:
- `GOOGLE_CLIENT_ID` — 없으면 이 라우터가 501. 로그인 자체가 불가.
- `AUTH_REQUIRED` — false면 쿠키 없는 요청이 dev 스텁으로 폴백(`deps.get_current_user`).
  덕분에 client_id를 넣고 로그인을 붙이는 동안에도 나머지 화면이 막히지 않는다.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import models
from .config import settings
from .db import get_db

router = APIRouter(prefix="/api/auth")

COOKIE_NAME = "kh_session"


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.session_secret, salt="kh-session")


def issue_session(response: Response, user_id: int) -> None:
    response.set_cookie(
        COOKIE_NAME, _serializer().dumps({"uid": user_id}),
        max_age=settings.session_max_age_days * 24 * 3600,
        httponly=True, secure=settings.cookie_secure, samesite="lax", path="/",
    )


def read_session(token: str | None) -> int | None:
    """쿠키 → user_id. 위조·만료면 None(호출부가 401을 결정한다)."""
    if not token:
        return None
    try:
        data = _serializer().loads(token, max_age=settings.session_max_age_days * 24 * 3600)
    except (BadSignature, SignatureExpired):
        return None
    return data.get("uid")


class GoogleLogin(BaseModel):
    credential: str        # Google Identity Services가 주는 ID 토큰(JWT)


@router.post("/google")
def google_login(payload: GoogleLogin, request: Request, response: Response,
                 db: Session = Depends(get_db)):
    if not settings.login_available:
        raise HTTPException(501, "GOOGLE_CLIENT_ID not configured")

    # 로그인 CSRF 방어 — 남의 사이트에서 우리 엔드포인트로 세션을 발급받지 못하게 한다.
    # ALLOWED_ORIGINS가 비면(개발) 검사하지 않는다.
    allowed = settings.allowed_origin_list
    if allowed:
        origin = (request.headers.get("origin") or "").rstrip("/")
        if origin not in allowed:
            raise HTTPException(403, "origin not allowed")

    from google.auth.transport import requests as g_requests
    from google.oauth2 import id_token

    try:
        info = id_token.verify_oauth2_token(
            payload.credential, g_requests.Request(), settings.google_client_id)
    except ValueError as e:                       # 서명·aud·만료 불일치
        raise HTTPException(401, f"invalid google token: {e}") from e
    if info.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise HTTPException(401, "invalid issuer")

    sub = info["sub"]
    user = (db.query(models.User)
            .filter_by(auth_provider="google", provider_sub=sub).first())
    if user is None:
        user = models.User(auth_provider="google", provider_sub=sub,
                           email=info.get("email", ""), name=info.get("name"),
                           picture=info.get("picture"))
        db.add(user)
    else:                                          # 프로필은 매 로그인 갱신
        user.email = info.get("email", user.email)
        user.name = info.get("name", user.name)
        user.picture = info.get("picture", user.picture)
    db.commit()
    db.refresh(user)

    issue_session(response, user.id)
    return {"id": user.id, "name": user.name, "email": user.email,
            "picture": user.picture, "level_band": user.level_band,
            "onboarded": user.level_band is not None}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}
