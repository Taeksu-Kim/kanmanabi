"""SRS 스케줄링 (SM-2 라이트). review_cards 한 장을 정답/오답으로 갱신."""
from datetime import datetime, timedelta, timezone


def schedule(card, correct: bool):
    now = datetime.now(timezone.utc)
    card.last_reviewed_at = now
    if correct:
        card.reps += 1
        if card.reps == 1:
            card.interval_days = 1
        elif card.reps == 2:
            card.interval_days = 6
        else:
            card.interval_days = max(1, round(card.interval_days * card.ease))
        card.ease = min(3.0, card.ease + 0.1)
    else:
        card.reps = 0
        card.lapses += 1
        card.interval_days = 0          # 오답 → 같은 세션에서 곧 다시
        card.ease = max(1.3, card.ease - 0.2)
    card.due_at = now + timedelta(days=card.interval_days)
    return card
