"""데이터 모델. 설계: docs/data_model.md.

공용 콘텐츠(episodes/questions/vocab)와 유저 상태(progress/attempts/review_cards)를 분리.
SRS 대상(question/vocab)은 review_cards 하나로 폴리모픽 관리.
"""
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


# ---------- 공용 콘텐츠 ----------
class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    ep_no: Mapped[str] = mapped_column(String(10), unique=True)   # "EP01"
    title: Mapped[str] = mapped_column(Text)
    chapter_range: Mapped[str | None] = mapped_column(String(50))
    level_band: Mapped[int | None] = mapped_column(Integer)
    youtube_id: Mapped[str | None] = mapped_column(String(20))
    order_index: Mapped[int] = mapped_column(Integer)            # 학습 경로 순서
    summary: Mapped[str | None] = mapped_column(Text)

    questions: Mapped[list["Question"]] = relationship(back_populates="episode")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 어휘문제=vocab_id / 문법문제=episode_id (둘 중 하나에 연결)
    episode_id: Mapped[int | None] = mapped_column(ForeignKey("episodes.id"))
    vocab_id: Mapped[int | None] = mapped_column(ForeignKey("vocab.id"))
    prompt: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[int] = mapped_column(Integer)             # 1~3 (★☆☆~★★★)
    qtype: Mapped[str] = mapped_column(String(20))               # fill_blank|transform|mcq|short
    choices: Mapped[list | None] = mapped_column(JSON)          # mcq용
    explanation: Mapped[str | None] = mapped_column(Text)        # 일본어 대조 해설
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str] = mapped_column(String(15), default="video_ep")  # video_ep(러프,재정의대상)|authored

    episode: Mapped["Episode"] = relationship(back_populates="questions")


class Vocab(Base):
    __tablename__ = "vocab"
    __table_args__ = (UniqueConstraint("word", "homonym_no", "pos", name="uq_vocab_whp"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    word: Mapped[str] = mapped_column(String(50))
    homonym_no: Mapped[int | None] = mapped_column(Integer)
    pos: Mapped[str] = mapped_column(String(30))
    level_band: Mapped[int] = mapped_column(Integer)            # 1~6
    guide: Mapped[str | None] = mapped_column(Text)             # 길잡이말
    ja: Mapped[list] = mapped_column(JSON)                      # 일본어 대역 배열
    hanja: Mapped[str | None] = mapped_column(String(50))       # 한자어만


class VocabEpisode(Base):
    """어휘↔EP 정렬. 스키마만 준비, 채우기는 후속(grep 빌드)."""
    __tablename__ = "vocab_episodes"

    vocab_id: Mapped[int] = mapped_column(ForeignKey("vocab.id"), primary_key=True)
    episode_id: Mapped[int] = mapped_column(ForeignKey("episodes.id"), primary_key=True)


# ---------- 유저 ----------
class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("auth_provider", "provider_sub", name="uq_user_provider"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    auth_provider: Mapped[str] = mapped_column(String(20), default="google")
    provider_sub: Mapped[str] = mapped_column(String(255))      # Google 'sub' (안정 식별자)
    email: Mapped[str] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(255))
    picture: Mapped[str | None] = mapped_column(Text)
    level_band: Mapped[int | None] = mapped_column(Integer)     # 온보딩 자기선택 can-do
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserEpisodeProgress(Base):
    __tablename__ = "user_episode_progress"
    __table_args__ = (UniqueConstraint("user_id", "episode_id", name="uq_progress_user_ep"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    episode_id: Mapped[int] = mapped_column(ForeignKey("episodes.id"))
    status: Mapped[str] = mapped_column(String(15), default="not_started")  # not_started|in_progress|completed
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Attempt(Base):
    """풀이 이벤트 로그(불변). 스트릭·통계는 created_at 에서 파생."""
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    item_type: Mapped[str] = mapped_column(String(10))          # question|vocab
    item_id: Mapped[int] = mapped_column(Integer)
    is_correct: Mapped[bool] = mapped_column()
    user_answer: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReviewCard(Base):
    """SRS 상태(유저×아이템). due_at<=now 카드 수 = '오늘 복습 N장' = 일일 훅."""
    __tablename__ = "review_cards"
    __table_args__ = (
        UniqueConstraint("user_id", "item_type", "item_id", name="uq_card_user_item"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    item_type: Mapped[str] = mapped_column(String(10))          # question|vocab
    item_id: Mapped[int] = mapped_column(Integer)
    ease: Mapped[float] = mapped_column(default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reps: Mapped[int] = mapped_column(Integer, default=0)
    lapses: Mapped[int] = mapped_column(Integer, default=0)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
