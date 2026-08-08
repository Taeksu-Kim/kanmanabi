from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # postgresql+psycopg://user:pass@db:5432/korean_helper
    database_url: str = "postgresql+psycopg://korean:change-me@db:5432/korean_helper"


settings = Settings()
