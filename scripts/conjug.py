"""한국어 활용엔진 (순수 로직). 규칙 활용만 — 불규칙은 None(제외).

받침처럼 결정론적이라 LLM에 안 맡긴다. 불규칙(ㄷ/ㅂ/ㅅ/ㅎ 받침·르)은 분류정보가
없으면 틀릴 수 있어 None으로 제외(틀린 답을 가르치지 않기 위함).
설계: docs/ep_grammar_map.md (T2). 테스트: scripts/test_conjug.py.
"""

# 종성(받침) 인덱스: ㄷ=7 ㅂ=17 ㅅ=19 ㅎ=27 (불규칙 후보)
_IRREG_JONG = {7, 17, 19, 27}


def _dec(ch):
    x = ord(ch) - 0xAC00
    return x // 588, (x % 588) // 28, x % 28


def _comp(cho, jung, jong):
    return chr(0xAC00 + cho * 588 + jung * 28 + jong)


def _hangul(ch):
    return "가" <= ch <= "힣"


def present_polite(word):
    """사전형(-다) → 현재 정중형(-아요/어요). 불규칙/비활용은 None."""
    if not isinstance(word, str) or not word.endswith("다") or len(word) < 2:
        return None
    stem = word[:-1]
    last = stem[-1]
    if not _hangul(last):
        return None
    cho, jung, jong = _dec(last)

    if last == "하":                          # 하다 → 해요
        return stem[:-1] + "해요"
    if jong in _IRREG_JONG:                   # ㄷ/ㅂ/ㅅ/ㅎ 받침 → 제외
        return None
    if cho == 5 and jung == 18 and jong == 0:  # 르 (ㄹ+ㅡ) → 제외
        return None

    harmony_a = jung in (0, 8)                # ㅏ/ㅗ → 아, else 어

    if jong != 0:                             # 받침 있음: + 아/어요
        add = _comp(11, 0 if harmony_a else 4, 0)   # 아 or 어
        return stem + add + "요"

    # 받침 없음 — 축약
    if jung == 18:                            # ㅡ 탈락
        a = False
        if len(stem) >= 2 and _hangul(stem[-2]):
            a = _dec(stem[-2])[1] in (0, 8)
        return stem[:-1] + _comp(cho, 0 if a else 4, 0) + "요"
    if jung in (0, 4, 1, 5):                  # ㅏㅓㅐㅔ → 그대로
        return stem + "요"
    if jung == 8:                             # ㅗ → ㅘ (오→와, 보→봐)
        return stem[:-1] + _comp(cho, 9, 0) + "요"
    if jung == 13:                            # ㅜ → ㅝ (주→줘)
        return stem[:-1] + _comp(cho, 14, 0) + "요"
    if jung == 20:                            # ㅣ → ㅕ (시→셔)
        return stem[:-1] + _comp(cho, 6, 0) + "요"
    if jung == 11:                            # ㅚ → ㅙ (되→돼)
        return stem[:-1] + _comp(cho, 10, 0) + "요"
    return None                               # 기타 모음(ㅑㅕㅛㅠ 등) → 제외
