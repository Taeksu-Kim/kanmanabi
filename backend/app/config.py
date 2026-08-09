from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # postgresql+psycopg://user:pass@db:5432/korean_helper
    database_url: str = "postgresql+psycopg://korean:change-me@db:5432/korean_helper"

    # Google OAuth 클라이언트 ID(공개값). 있으면 /api/auth/google 로그인이 동작한다.
    google_client_id: str = ""
    # 로그인을 강제할지. False면 쿠키 없는 요청이 dev 스텁 유저로 폴백한다.
    # client_id를 설정해도 이 값이 False면 로컬 개발이 막히지 않는다 — 운영에서만 true.
    auth_required: bool = False
    # 세션 쿠키 서명 키. 운영에서는 반드시 환경변수로 주입(바뀌면 전체 로그아웃).
    session_secret: str = "dev-insecure-secret"
    session_max_age_days: int = 30
    # 로컬 http 개발에서는 Secure 쿠키가 전송되지 않으므로 끈다.
    cookie_secure: bool = False
    # 로그인 요청을 허용할 Origin(쉼표 구분). 비면 검사하지 않는다(개발).
    # 운영에서 반드시 설정 — 다른 사이트가 우리 로그인 엔드포인트로 세션을 발급받지 못하게 한다.
    allowed_origins: str = ""

    @property
    def allowed_origin_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def login_available(self) -> bool:
        """Google 로그인 엔드포인트가 동작하는가 (client_id 유무)."""
        return bool(self.google_client_id)


settings = Settings()
