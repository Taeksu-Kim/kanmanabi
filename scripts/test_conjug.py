"""한국어 활용엔진 테스트 (TDD). 실행: pytest scripts/test_conjug.py

present_polite: 사전형(-다) → 현재 정중형(-아요/어요). 규칙만, 불규칙은 None(제외).
"""
import pytest

import conjug as c


@pytest.mark.parametrize("word,expected", [
    # 받침 있음 — 모음조화 (ㅏ/ㅗ→아요, else 어요)
    ("먹다", "먹어요"), ("읽다", "읽어요"), ("살다", "살아요"),
    ("앉다", "앉아요"), ("신다", "신어요"),
    # 하다 → 해요
    ("하다", "해요"), ("공부하다", "공부해요"), ("좋아하다", "좋아해요"),
    # 받침 없음 — 축약
    ("가다", "가요"), ("서다", "서요"),
    ("오다", "와요"), ("보다", "봐요"),
    ("주다", "줘요"), ("배우다", "배워요"),
    ("마시다", "마셔요"), ("기다리다", "기다려요"),
    ("되다", "돼요"), ("보내다", "보내요"),
    # ㅡ 탈락
    ("쓰다", "써요"), ("크다", "커요"),
    ("예쁘다", "예뻐요"), ("바쁘다", "바빠요"), ("아프다", "아파요"),
])
def test_present_polite_regular(word, expected):
    assert c.present_polite(word) == expected


@pytest.mark.parametrize("word", [
    # 불규칙 후보(ㄷ/ㅂ/ㅅ/ㅎ 받침) — 확실치 않으니 제외(None)
    "듣다", "춥다", "짓다", "빨갛다",
    # 르 — 불규칙/러 애매 → 제외
    "모르다", "부르다",
    # 비활용/비한글
    "책", "cafe",
])
def test_irregular_or_invalid_excluded(word):
    assert c.present_polite(word) is None
    assert c.past_polite(word) is None
    assert c.honorific(word) is None


@pytest.mark.parametrize("word,expected", [
    ("먹다", "먹어"), ("가다", "가"), ("하다", "해"), ("오다", "와"),
    ("쓰다", "써"), ("마시다", "마셔"),
])
def test_present_informal(word, expected):
    assert c.present_informal(word) == expected


@pytest.mark.parametrize("word,expected", [
    ("먹다", "먹었어요"), ("가다", "갔어요"), ("하다", "했어요"), ("오다", "왔어요"),
    ("앉다", "앉았어요"), ("쓰다", "썼어요"), ("마시다", "마셨어요"), ("되다", "됐어요"),
])
def test_past_polite(word, expected):
    assert c.past_polite(word) == expected


@pytest.mark.parametrize("word,expected", [
    ("가다", "가세요"), ("먹다", "먹으세요"), ("살다", "사세요"),
    ("하다", "하세요"), ("읽다", "읽으세요"), ("되다", "되세요"),
])
def test_honorific(word, expected):
    assert c.honorific(word) == expected


@pytest.mark.parametrize("word,expected", [
    ("먹다", "먹었었어요"), ("가다", "갔었어요"), ("하다", "했었어요"), ("오다", "왔었어요"),
])
def test_past_past(word, expected):
    assert c.past_past_polite(word) == expected


@pytest.mark.parametrize("word,pos,expected", [
    ("먹다", "동사", "먹는"), ("가다", "동사", "가는"), ("살다", "동사", "사는"),
    ("만들다", "동사", "만드는"),
    ("작다", "형용사", "작은"), ("크다", "형용사", "큰"), ("예쁘다", "형용사", "예쁜"),
    ("길다", "형용사", "긴"),
])
def test_adnominal_present(word, pos, expected):
    assert c.adnominal_present(word, pos) == expected
