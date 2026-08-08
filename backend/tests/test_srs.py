from datetime import datetime, timezone

import pytest

from app.srs import schedule


class Card:
    ease = 2.5
    interval_days = 0
    reps = 0
    lapses = 0
    due_at = None
    last_reviewed_at = None


def test_correct_advances_interval():
    c = Card()
    schedule(c, True)
    assert c.reps == 1 and c.interval_days == 1
    schedule(c, True)
    assert c.reps == 2 and c.interval_days == 6
    schedule(c, True)
    # interval = round(6 * ease_before_bump=2.7) = 16 ; ease는 계산 후 2.8로 상승
    assert c.reps == 3 and c.interval_days == 16 and c.ease == pytest.approx(2.8)


def test_wrong_resets_and_due_now():
    c = Card()
    c.reps, c.interval_days, c.ease = 3, 6, 2.5
    schedule(c, False)
    assert c.reps == 0 and c.lapses == 1 and c.interval_days == 0
    assert c.ease == 2.3  # -0.2
    assert c.due_at <= datetime.now(timezone.utc)
