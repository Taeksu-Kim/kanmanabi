from app import models
from app.conjugation_logic import forms


def test_three_base_logic_covers_regular_and_irregular_patterns():
    assert forms("가다") == {"stem": "가", "ae": "가", "eu": "가"}
    assert forms("먹다") == {"stem": "먹", "ae": "먹어", "eu": "먹으"}
    assert forms("듣다") == {"stem": "듣", "ae": "들어", "eu": "들으"}
    assert forms("춥다") == {"stem": "춥", "ae": "추워", "eu": "추우"}
    assert forms("다르다") == {"stem": "다르", "ae": "달라", "eu": "다르"}
    assert forms("쓰다") == {"stem": "쓰", "ae": "써", "eu": "쓰"}
    assert forms("길다") == {"stem": "길", "ae": "길어", "eu": "길"}
    assert forms("그렇다") == {"stem": "그렇", "ae": "그래", "eu": "그러"}


def _add_conjugation_vocab(client):
    db = client.db()
    db.add_all([
        models.Vocab(word="듣다", homonym_no=None, pos="동사", level_band=1,
                     guide=None, ja=["聞く"], hanja=None),
        models.Vocab(word="춥다", homonym_no=None, pos="형용사", level_band=1,
                     guide=None, ja=["寒い"], hanja=None),
    ])
    db.commit()
    db.close()


def test_three_form_answer_records_each_form_and_reviews_mistakes(client):
    _add_conjugation_vocab(client)
    nxt = client.get("/api/conjugation/next?level=1").json()
    assert nxt["drill"]["word"] in {"듣다", "춥다"}

    if nxt["drill"]["word"] == "듣다":
        payload = {"vocab_id": nxt["drill"]["id"], "stem": "듣", "ae": "듣어", "eu": "듣으"}
        response = client.post("/api/conjugation/answer", json=payload).json()
        assert response["results"]["stem"]["correct"] is True
        assert response["results"]["ae"]["answer"] == "들어"
        assert response["results"]["eu"]["answer"] == "들으"
        assert response["rule"]["label_ja"] == "ㄷ不規則"
    else:
        payload = {"vocab_id": nxt["drill"]["id"], "stem": "춥", "ae": "춥어", "eu": "춥으"}
        response = client.post("/api/conjugation/answer", json=payload).json()
        assert response["results"]["ae"]["answer"] == "추워"
        assert response["results"]["eu"]["answer"] == "추우"

    db = client.db()
    attempts = db.query(models.Attempt).filter(models.Attempt.item_type.like("conj_%")).all()
    cards = db.query(models.ReviewCard).filter(models.ReviewCard.item_type.like("conj_%")).all()
    assert len(attempts) == 3
    assert len(cards) == 3
    assert sum(card.lapses for card in cards) == 2
    db.close()


def test_conjugation_summary_derives_weakness_from_attempts(client):
    _add_conjugation_vocab(client)
    nxt = client.get("/api/conjugation/next?level=1").json()["drill"]
    client.post("/api/conjugation/answer", json={
        "vocab_id": nxt["id"], "stem": "x", "ae": "x", "eu": "x",
    })
    summary = client.get("/api/conjugation/summary").json()
    assert summary["due_count"] == 3
    assert summary["weakest_rule"] in {"ㄷ不規則", "ㅂ不規則"}
