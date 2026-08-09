import json

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

# JSON 컬럼(vocab.ja 등)을 유니코드 그대로 저장한다. 기본값(ensure_ascii=True)이면
# 일본어가 \uXXXX로 저장돼 단어장 검색의 LIKE가 걸리지 않는다.
engine = create_engine(settings.database_url, pool_pre_ping=True,
                       json_serializer=lambda o: json.dumps(o, ensure_ascii=False))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """모델 베이스. 실제 테이블은 데이터 모델 확정 후 추가."""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
