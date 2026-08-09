"""widen questions.qtype to 40

Revision ID: 4290c0a76c27
Revises: 9428a550ee2e
Create Date: 2026-08-09 20:01:37.816594

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4290c0a76c27'
down_revision: Union[str, None] = '9428a550ee2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # sqlite는 ALTER TYPE을 지원하지 않지만 길이 제한 자체를 무시하므로 건너뛴다.
    if op.get_bind().dialect.name != "sqlite":
        op.alter_column("questions", "qtype",
                        existing_type=sa.String(20), type_=sa.String(40),
                        existing_nullable=False)


def downgrade() -> None:
    if op.get_bind().dialect.name != "sqlite":
        op.alter_column("questions", "qtype",
                        existing_type=sa.String(40), type_=sa.String(20),
                        existing_nullable=False)
