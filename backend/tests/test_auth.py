"""세션 쿠키와 개발 폴백 (docs/data_model.md §인증)."""
import pytest

from app import auth, models
from app.config import settings


def test_dev_mode_falls_back_without_cookie(client):
    """AUTH_REQUIRED=false(개발) → 쿠키 없이도 스텁 유저로 동작."""
    assert settings.auth_required is False
    assert client.get("/api/me").status_code == 200


def test_client_id_alone_does_not_lock_dev(client, monkeypatch):
    """client_id만 넣어도 개발이 막히지 않는다 — 로그인 붙이는 동안 필요한 성질."""
    monkeypatch.setattr(settings, "google_client_id", "x.apps.googleusercontent.com")
    assert client.get("/api/me").status_code == 200
    # 대신 로그인 엔드포인트는 살아난다(토큰이 가짜라 401)
    assert client.post("/api/auth/google", json={"credential": "bogus"}).status_code == 401


def test_google_login_disabled_in_dev(client):
    assert client.post("/api/auth/google", json={"credential": "x"}).status_code == 501


def test_session_cookie_roundtrip():
    token = auth._serializer().dumps({"uid": 42})
    assert auth.read_session(token) == 42
    assert auth.read_session(None) is None
    assert auth.read_session("tampered.token.value") is None


def test_tampered_cookie_rejected():
    """서명이 다르면 무효 — 쿠키 위조로 남의 계정이 되지 않는다."""
    forged = auth.URLSafeTimedSerializer("other-secret", salt="kh-session").dumps({"uid": 1})
    assert auth.read_session(forged) is None


def test_expired_cookie_rejected(monkeypatch):
    """만료 시각을 넘긴 쿠키는 거부. itsdangerous가 쓰는 시계를 미래로 옮겨 확인."""
    import time as _time

    import itsdangerous.timed as itd
    token = auth._serializer().dumps({"uid": 7})
    later = _time.time() + (settings.session_max_age_days + 1) * 24 * 3600
    monkeypatch.setattr(itd.time, "time", lambda: later)
    assert auth.read_session(token) is None


def test_cookie_identifies_user(client):
    """쿠키의 uid가 실제 조회 유저를 결정한다."""
    db = client.db()
    other = models.User(auth_provider="google", provider_sub="sub-2",
                        email="other@example.com", name="Other", level_band=3)
    db.add(other); db.commit(); db.refresh(other); oid = other.id; db.close()

    client.cookies.set(auth.COOKIE_NAME, auth._serializer().dumps({"uid": oid}))
    me = client.get("/api/me").json()
    assert me["id"] == oid and me["level_band"] == 3
    client.cookies.clear()


@pytest.mark.parametrize("path", ["/api/me", "/api/learn/summary", "/api/vocab",
                                  "/api/study/due", "/api/episodes"])
def test_401_when_auth_required_and_no_cookie(client, monkeypatch, path):
    """운영 설정(AUTH_REQUIRED=true)에서는 쿠키 없으면 전 엔드포인트 401 — 폴백이 새지 않는다."""
    monkeypatch.setattr(settings, "auth_required", True)
    assert client.get(path).status_code == 401


def test_logout_clears_cookie(client):
    r = client.post("/api/auth/logout")
    assert r.status_code == 200
    assert "kh_session" in r.headers.get("set-cookie", "")


def test_origin_check_blocks_foreign_site(client, monkeypatch):
    """ALLOWED_ORIGINS 설정 시 다른 사이트의 로그인 요청은 403 (로그인 CSRF 방어)."""
    monkeypatch.setattr(settings, "google_client_id", "x.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "allowed_origins", "http://localhost:5173")

    bad = client.post("/api/auth/google", json={"credential": "t"},
                      headers={"Origin": "https://evil.example"})
    assert bad.status_code == 403
    # 허용 Origin이면 검증 단계까지 진행된다(토큰이 가짜라 401)
    ok = client.post("/api/auth/google", json={"credential": "t"},
                     headers={"Origin": "http://localhost:5173/"})   # 끝 슬래시 허용
    assert ok.status_code == 401


def test_origin_check_skipped_when_unset(client, monkeypatch):
    """개발(미설정)에서는 Origin 검사를 하지 않는다."""
    monkeypatch.setattr(settings, "google_client_id", "x.apps.googleusercontent.com")
    assert client.post("/api/auth/google", json={"credential": "t"},
                       headers={"Origin": "https://anything"}).status_code == 401


def test_google_verify_dependencies_importable():
    """google-auth의 requests 트랜스포트가 실제로 import되는지.

    requirements에 [requests] extra를 빠뜨리면 로그인 시점에야 ImportError가 난다.
    로컬에는 requests가 다른 패키지 의존으로 깔려 있어 드러나지 않으므로 명시적으로 확인한다.
    """
    from google.auth.transport import requests as g_requests
    from google.oauth2 import id_token
    assert callable(id_token.verify_oauth2_token)
    assert g_requests.Request is not None
