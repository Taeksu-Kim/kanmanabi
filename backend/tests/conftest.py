"""테스트 하베스 — 인메모리 sqlite + TestClient. 각 테스트마다 새 DB에 최소 시드."""
import json

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
    ep = models.Episode(ep_no="EP01", title="EP01 지시어", order_index=1)
    db.add(ep)
    db.flush()
    db.add_all([
        # 문법문항 A: vocab 연결 있음(조사) — 어휘 세션에 섞이던 유형
        models.Question(episode_id=ep.id, vocab_id=v2.id, qtype="particle_iga", prompt="학교( )",
                        answer="가", choices=["이", "가"], difficulty=1, source="generated"),
        # 문법문항 B: vocab 연결 없음(뉘앙스) — inner join 시절 절대 안 나오던 유형
        models.Question(episode_id=ep.id, vocab_id=None, qtype="nuance_go_seo",
                        prompt="밥을 먹( ) 학교에 가요.", answer="고", choices=["고", "어서"],
                        difficulty=3, source="authored"),
        # 공백 포함 정답 — 채점 정규화 대상
        models.Question(episode_id=ep.id, vocab_id=None, qtype="conjug_neg_an",
                        prompt="앉다 → ?（否定(안)）", answer="안 앉아요",
                        choices=["안 앉아요", "안 앉어요"], difficulty=2, source="generated"),
    ])
    db.commit()


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool,
                           json_serializer=lambda o: json.dumps(o, ensure_ascii=False))
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
    c = TestClient(app)
    c.db = TestSession          # 테스트에서 DB 직접 확인용 (응답에 안 실리는 컬럼 검증)
    yield c
    app.dependency_overrides.clear()
