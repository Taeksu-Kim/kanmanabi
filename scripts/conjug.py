"""한국어 활용엔진 (순수 로직). 규칙 활용만 — 불규칙은 None(제외).

받침처럼 결정론적이라 LLM에 안 맡긴다. 불규칙(ㄷ/ㅂ/ㅅ/ㅎ 받침·르)은 분류정보가
없으면 틀릴 수 있어 None으로 제외(틀린 답을 가르치지 않기 위함).
설계: docs/ep_grammar_map.md (T2). 테스트: scripts/test_conjug.py.

폼:
  present_informal (반말, EP09)  : 먹다→먹어
  present_polite   (정중, EP15)  : 먹다→먹어요
  past_polite      (과거, EP13)  : 먹다→먹었어요
  honorific        (경어, EP12)  : 먹다→먹으세요
"""
_IRREG_JONG = {7, 17, 19, 27}   # ㄷ/ㅂ/ㅅ/ㅎ 받침 (불규칙 후보)


def _dec(ch):
    x = ord(ch) - 0xAC00
    return x // 588, (x % 588) // 28, x % 28


def _comp(cho, jung, jong):
    return chr(0xAC00 + cho * 588 + jung * 28 + jong)


def _hangul(ch):
    return "가" <= ch <= "힣"


def _excluded(cho, jung, jong):
    if jong in _IRREG_JONG:                     # ㄷ/ㅂ/ㅅ/ㅎ
        return True
    if cho == 5 and jung == 18 and jong == 0:   # 르 (ㄹ+ㅡ)
        return True
    return False


def _stem_form(word):
    """반말(어/아) 형태 — 요 없는 형. 불규칙/비활용은 None."""
    if not isinstance(word, str) or not word.endswith("다") or len(word) < 2:
        return None
    stem = word[:-1]
    last = stem[-1]
    if not _hangul(last):
        return None
    cho, jung, jong = _dec(last)

    if last == "하":                              # 하 → 해
        return stem[:-1] + "해"
    if _excluded(cho, jung, jong):
        return None

    harmony_a = jung in (0, 8)
    if jong != 0:                                 # 받침: + 아/어
        return stem + _comp(11, 0 if harmony_a else 4, 0)
    if jung == 18:                                # ㅡ 탈락
        a = len(stem) >= 2 and _hangul(stem[-2]) and _dec(stem[-2])[1] in (0, 8)
        return stem[:-1] + _comp(cho, 0 if a else 4, 0)
    if jung in (0, 4, 1, 5):                      # ㅏㅓㅐㅔ → 그대로
        return stem
    if jung == 8:                                 # ㅗ → ㅘ
        return stem[:-1] + _comp(cho, 9, 0)
    if jung == 13:                                # ㅜ → ㅝ
        return stem[:-1] + _comp(cho, 14, 0)
    if jung == 20:                                # ㅣ → ㅕ
        return stem[:-1] + _comp(cho, 6, 0)
    if jung == 11:                                # ㅚ → ㅙ
        return stem[:-1] + _comp(cho, 10, 0)
    return None


def present_informal(word):                        # EP09
    return _stem_form(word)


def present_polite(word):                          # EP15
    s = _stem_form(word)
    return s + "요" if s else None


def past_polite(word):                             # EP13
    s = _stem_form(word)
    if not s:
        return None
    cho, jung, _ = _dec(s[-1])
    return s[:-1] + _comp(cho, jung, 20) + "어요"    # 마지막 음절 + ㅆ + 어요


def past_past_polite(word):                        # EP14 대과거 (-ㅆ었어요)
    p = past_polite(word)
    return p[:-2] + "었어요" if p else None           # 어요 → 었어요 (먹었어요→먹었었어요)


def adnominal_present(word, pos):                  # EP20 관형형 현재 (동사 -는 / 형용사 -(으)ㄴ)
    if not isinstance(word, str) or not word.endswith("다") or len(word) < 2:
        return None
    stem = word[:-1]
    last = stem[-1]
    if not _hangul(last):
        return None
    cho, jung, jong = _dec(last)
    if _excluded(cho, jung, jong):
        return None
    if pos == "동사":
        if jong == 8:                              # ㄹ 탈락: 살→사는
            return stem[:-1] + _comp(cho, jung, 0) + "는"
        return stem + "는"
    if pos == "형용사":
        if jong == 8:                              # ㄹ→ㄴ: 길→긴
            return stem[:-1] + _comp(cho, jung, 4)
        if jong == 0:                              # +ㄴ: 크→큰, 예쁘→예쁜
            return stem[:-1] + _comp(cho, jung, 4)
        return stem + "은"                          # 받침: 작→작은
    return None


def honorific(word):                               # EP12
    if not isinstance(word, str) or not word.endswith("다") or len(word) < 2:
        return None
    stem = word[:-1]
    last = stem[-1]
    if not _hangul(last):
        return None
    cho, jung, jong = _dec(last)
    if last == "하":
        return stem + "세요"
    if _excluded(cho, jung, jong):
        return None
    if jong == 0:
        return stem + "세요"
    if jong == 8:                                  # ㄹ 탈락 (살→사세요)
        return stem[:-1] + _comp(cho, jung, 0) + "세요"
    return stem + "으세요"
