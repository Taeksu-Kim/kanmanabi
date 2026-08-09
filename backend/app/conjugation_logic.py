"""Deterministic three-base Korean conjugation logic for the drill API.

The three answers mirror the Japanese teaching pattern used by 3-type-test:
stem (다 removal), 아/어 base, and the base used before -(으)면.
Ambiguous irregular candidates are excluded rather than guessed.
"""

IRREGULAR = {
    "걷다": "ㄷ", "싣다": "ㄷ", "듣다": "ㄷ",
    "가깝다": "ㅂ", "가볍다": "ㅂ", "고맙다": "ㅂ", "덥다": "ㅂ", "맵다": "ㅂ",
    "무겁다": "ㅂ", "반갑다": "ㅂ", "쉽다": "ㅂ", "싱겁다": "ㅂ", "아름답다": "ㅂ",
    "어렵다": "ㅂ", "춥다": "ㅂ", "귀엽다": "ㅂ", "그립다": "ㅂ", "눕다": "ㅂ",
    "더럽다": "ㅂ", "두껍다": "ㅂ", "뜨겁다": "ㅂ", "무섭다": "ㅂ", "부끄럽다": "ㅂ",
    "부드럽다": "ㅂ", "부럽다": "ㅂ", "새롭다": "ㅂ", "시끄럽다": "ㅂ", "어둡다": "ㅂ",
    "외롭다": "ㅂ", "즐겁다": "ㅂ", "차갑다": "ㅂ", "줍다": "ㅂ",
    "돕다": "ㅂ와", "곱다": "ㅂ와",
    "낫다": "ㅅ", "짓다": "ㅅ", "잇다": "ㅅ", "붓다": "ㅅ", "젓다": "ㅅ",
    "그렇다": "ㅎ", "어떻다": "ㅎ", "이렇다": "ㅎ", "저렇다": "ㅎ",
    "까맣다": "ㅎ", "노랗다": "ㅎ", "빨갛다": "ㅎ", "파랗다": "ㅎ", "하얗다": "ㅎ",
    "고르다": "르", "다르다": "르", "모르다": "르", "부르다": "르", "빠르다": "르",
    "게으르다": "르", "기르다": "르", "누르다": "르", "마르다": "르", "바르다": "르",
    "서두르다": "르", "오르다": "르", "자르다": "르", "지르다": "르", "흐르다": "르",
}

REGULAR_CANDIDATES = {
    "닫다", "받다", "믿다", "얻다", "입다", "갈아입다", "씹다", "뽑다", "잡다", "접다",
    "좁다", "업다", "씻다", "웃다", "벗다", "빗다", "솟다", "넣다", "좋다", "놓다",
    "쌓다", "낳다", "들르다", "따르다", "치르다",
}

_IRREG_JONG = {7, 17, 19, 27}


def _dec(ch: str):
    value = ord(ch) - 0xAC00
    return value // 588, (value % 588) // 28, value % 28


def _comp(cho: int, jung: int, jong: int):
    return chr(0xAC00 + cho * 588 + jung * 28 + jong)


def _hangul(ch: str):
    return "가" <= ch <= "힣"


def _drop_jong(stem: str):
    cho, jung, _ = _dec(stem[-1])
    return stem[:-1] + _comp(cho, jung, 0)


def _to_rieul(stem: str):
    cho, jung, _ = _dec(stem[-1])
    return stem[:-1] + _comp(cho, jung, 8)


def _kind(word: str, cho: int, jung: int, jong: int):
    candidate = jong in _IRREG_JONG or (cho == 5 and jung == 18 and jong == 0)
    if not candidate:
        return "reg"
    if word in IRREGULAR:
        return IRREGULAR[word]
    return "reg" if word in REGULAR_CANDIDATES else None


def _ah_uh(base: str):
    return base + ("아" if _dec(base[-1])[1] in (0, 8) else "어")


def _ae_base(word: str):
    stem = word[:-1]
    cho, jung, jong = _dec(stem[-1])
    if stem[-1] == "하":
        return stem[:-1] + "해"
    kind = _kind(word, cho, jung, jong)
    if kind is None:
        return None
    if kind in ("ㅂ", "ㅂ와"):
        return _drop_jong(stem) + ("와" if kind == "ㅂ와" else "워")
    if kind == "ㅅ":
        return _ah_uh(_drop_jong(stem))
    if kind == "ㄷ":
        return _ah_uh(_to_rieul(stem))
    if kind == "ㅎ":
        base = _drop_jong(stem)
        base_cho, base_jung, _ = _dec(base[-1])
        return base[:-1] + _comp(base_cho, 3 if base_jung == 2 else 1, 0)
    if kind == "르":
        head = stem[:-1]
        head_cho, head_jung, _ = _dec(head[-1])
        head = head[:-1] + _comp(head_cho, head_jung, 8)
        return head + ("라" if head_jung in (0, 8) else "러")
    harmony_a = jung in (0, 8)
    if jong:
        return stem + ("아" if harmony_a else "어")
    if jung == 18:
        use_a = len(stem) >= 2 and _hangul(stem[-2]) and _dec(stem[-2])[1] in (0, 8)
        return stem[:-1] + _comp(cho, 0 if use_a else 4, 0)
    if jung in (0, 4, 1, 5):
        return stem
    contractions = {8: 9, 13: 14, 20: 6, 11: 10}
    if jung in contractions:
        return stem[:-1] + _comp(cho, contractions[jung], 0)
    return None


def _eu_base(word: str):
    stem = word[:-1]
    cho, jung, jong = _dec(stem[-1])
    kind = _kind(word, cho, jung, jong)
    if kind is None:
        return None
    if kind in ("ㅂ", "ㅂ와"):
        return _drop_jong(stem) + "우"
    if kind == "ㄷ":
        return _to_rieul(stem) + "으"
    if kind == "ㅅ":
        return _drop_jong(stem) + "으"
    if kind == "ㅎ":
        return _drop_jong(stem)
    if kind == "르":
        return stem
    if jong == 0 or jong == 8:
        return stem
    return stem + "으"


def forms(word: str):
    if not isinstance(word, str) or len(word) < 2 or not word.endswith("다") or not _hangul(word[-2]):
        return None
    ae = _ae_base(word)
    eu = _eu_base(word)
    if ae is None or eu is None:
        return None
    return {"stem": word[:-1], "ae": ae, "eu": eu}


def rule_for(word: str):
    kind = IRREGULAR.get(word)
    if kind:
        normalized = "ㅂ" if kind == "ㅂ와" else kind
        return {
            "id": f"irregular_{normalized}",
            "label_ja": f"{normalized}不規則",
            "explanation_ja": {
                "ㄷ": "母音の前ではㄷがㄹに変わります。",
                "ㅂ": "母音の前ではㅂが取れて、우／오が加わります。",
                "ㅅ": "母音の前ではㅅが取れます。",
                "ㅎ": "母音の前ではㅎが取れ、母音が縮約します。",
                "르": "아／어形では르がㄹ라／ㄹ러に変わります。",
            }[normalized],
        }
    stem = word[:-1]
    _, jung, jong = _dec(stem[-1])
    if stem[-1] == "하":
        return {"id": "hada", "label_ja": "하다活用", "explanation_ja": "하다の아／어形は해になります。"}
    if jung == 18 and jong == 0:
        return {"id": "eu_drop", "label_ja": "ㅡ脱落", "explanation_ja": "아／어形ではㅡが取れ、前の母音に合わせます。"}
    if jong == 0 and jung in (8, 11, 13, 20):
        return {"id": "vowel_contraction", "label_ja": "母音縮約", "explanation_ja": "母音が続くと、一つの音節に縮まります。"}
    if jong == 8:
        return {"id": "rieul_stem", "label_ja": "ㄹ語幹", "explanation_ja": "ㄹ語幹の後では으を付けません。"}
    return {"id": "regular", "label_ja": "基本活用", "explanation_ja": "語幹の母音とパッチムに合わせて形を作ります。"}
