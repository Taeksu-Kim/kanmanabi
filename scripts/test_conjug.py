"""한국어 활용엔진 테스트 (TDD). 실행: pytest scripts/test_c.py

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
    # 분류표(irregular.py)에 없는 불규칙 후보 — 확실치 않으니 제외(None)
    "묻다", "굽다", "푸르다", "이르다",
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


@pytest.mark.parametrize("word,expected", [("먹다", "먹"), ("가다", "가"), ("공부하다", "공부하")])
def test_stem(word, expected):
    assert c.stem(word) == expected


@pytest.mark.parametrize("word,expected", [
    ("먹다", "먹어 주세요"), ("가다", "가 주세요"), ("하다", "해 주세요"),
])
def test_request(word, expected):
    assert c.request(word) == expected


@pytest.mark.parametrize("word,expected", [("먹다", "안 먹어요"), ("가다", "안 가요")])
def test_negation_short(word, expected):
    assert c.negation_short(word) == expected


@pytest.mark.parametrize("word,expected", [
    ("먹다", "먹지 않아요"), ("가다", "가지 않아요"), ("듣다", "듣지 않아요"),  # 불규칙 무관
])
def test_negation_long(word, expected):
    assert c.negation_long(word) == expected


@pytest.mark.parametrize("word,expected", [
    ("먹다", "먹은"), ("가다", "간"), ("살다", "산"), ("만들다", "만든"), ("보다", "본"),
])
def test_adnominal_past(word, expected):
    assert c.adnominal_past(word) == expected


# --- 불규칙 활용 (irregular.py 분류표) ---
IRREG_CASES = [
    # word, 반말, 정중, 과거, 경어, 과거관형/-(으)ㄴ
    ("춥다",   "추워", "추워요", "추웠어요", "추우세요", "추운"),
    ("어렵다", "어려워", "어려워요", "어려웠어요", "어려우세요", "어려운"),
    ("돕다",   "도와", "도와요", "도왔어요", "도우세요", "도운"),
    ("줍다",   "주워", "주워요", "주웠어요", "주우세요", "주운"),
    ("걷다",   "걸어", "걸어요", "걸었어요", "걸으세요", "걸은"),
    ("싣다",   "실어", "실어요", "실었어요", "실으세요", "실은"),
    ("낫다",   "나아", "나아요", "나았어요", "나으세요", "나은"),
    ("짓다",   "지어", "지어요", "지었어요", "지으세요", "지은"),
    ("붓다",   "부어", "부어요", "부었어요", "부으세요", "부은"),
    ("그렇다", "그래", "그래요", "그랬어요", "그러세요", "그런"),
    ("빨갛다", "빨개", "빨개요", "빨갰어요", "빨가세요", "빨간"),
    ("하얗다", "하얘", "하얘요", "하얬어요", "하야세요", "하얀"),
    ("모르다", "몰라", "몰라요", "몰랐어요", "모르세요", "모른"),
    ("부르다", "불러", "불러요", "불렀어요", "부르세요", "부른"),
    ("빠르다", "빨라", "빨라요", "빨랐어요", "빠르세요", "빠른"),
    ("흐르다", "흘러", "흘러요", "흘렀어요", "흐르세요", "흐른"),
]


def test_irregular_forms():
    for w, inf, pol, past, hon, eun in IRREG_CASES:
        assert c.present_informal(w) == inf, (w, c.present_informal(w), inf)
        assert c.present_polite(w) == pol, (w, c.present_polite(w), pol)
        assert c.past_polite(w) == past, (w, c.past_polite(w), past)
        assert c.honorific(w) == hon, (w, c.honorific(w), hon)
        assert c.adnominal_past(w) == eun, (w, c.adnominal_past(w), eun)


def test_regular_lookalikes_still_regular():
    # 후보 받침이지만 규칙 — REGULAR 목록으로 이제 생성된다
    assert c.present_polite("입다") == "입어요"
    assert c.present_polite("웃다") == "웃어요"
    assert c.present_polite("좋다") == "좋아요"
    assert c.honorific("받다") == "받으세요"
    assert c.adnominal_past("잡다") == "잡은"


def test_unclassified_still_excluded():
    # 분류표에 없는 후보는 계속 제외 (틀린 답 방지)
    assert c.present_polite("묻다") is None
    assert c.present_polite("굽다") is None
    assert c.honorific("푸르다") is None


def test_adnominal_present_irregular():
    assert c.adnominal_present("걷다", "동사") == "걷는"
    assert c.adnominal_present("짓다", "동사") == "짓는"
    assert c.adnominal_present("모르다", "동사") == "모르는"
    assert c.adnominal_present("춥다", "형용사") == "추운"


def test_eu_stem_detection():
    """EP10 ㅡ어간 판정 — 르(르불규칙)는 제외."""
    from gen_conjug import _is_eu
    assert _is_eu("쓰다") and _is_eu("바쁘다") and _is_eu("예쁘다")
    assert not _is_eu("모르다") and not _is_eu("먹다") and not _is_eu("가다")
    assert c.present_polite("바쁘다") == "바빠요"
    assert c.present_polite("예쁘다") == "예뻐요"
