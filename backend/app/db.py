from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """모델 베이스. 실제 테이블은 데이터 모델 확정 후 추가."""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
