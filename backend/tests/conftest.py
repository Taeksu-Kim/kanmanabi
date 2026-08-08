"""테스트 하베스 — 인메모리 sqlite + TestClient. 각 테스트마다 새 DB에 최소 시드."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app import models


def _seed(db):
    v1 = models.Vocab(word="가게", homonym_no=None, pos="명사", level_band=1,
                      guide="가게에 가다", ja=["みせ【店】"], hanja=None)
    v2 = models.Vocab(word="학교", homonym_no=None, pos="명사", level_band=1,
                      guide="학교에 가다", ja=["がっこう【学校】"], hanja="學校")
    db.add_all([v1, v2])
    db.flush()
    db.add_all([
        models.Question(vocab_id=v1.id, qtype="word_to_ja", prompt="가게",
                        answer="みせ【店】", choices=["みせ【店】", "がっこう【学校】", "はん【飯】", "みず【水】"],
                        difficulty=1, source="generated"),
        models.Question(vocab_id=v2.id, qtype="ja_to_word", prompt="がっこう【学校】",
                        answer="학교", choices=["학교", "가게", "학생", "교실"],
                        difficulty=2, source="generated"),
    ])
    db.commit()


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    db = TestSession(); _seed(db); db.close()

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
