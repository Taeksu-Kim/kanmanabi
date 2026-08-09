"""한국어 활용엔진 (순수 로직).

받침처럼 결정론적이라 LLM에 안 맡긴다. 불규칙(ㄷ/ㅂ/ㅅ/ㅎ 받침·르)은 어간 형태만으론
판정 불가라 `irregular.py` 분류표를 참조한다. 표에 없는 후보는 여전히 None(제외) —
틀린 답을 가르치지 않기 위함.
설계: docs/ep_grammar_map.md (T2). 테스트: scripts/test_conjug.py.

폼:
  present_informal (반말, EP09)  : 먹다→먹어
  present_polite   (정중, EP15)  : 먹다→먹어요
  past_polite      (과거, EP13)  : 먹다→먹었어요
  honorific        (경어, EP12)  : 먹다→먹으세요
"""
import irregular

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


def _kind(word, cho, jung, jong):
    """불규칙 후보면 분류표 조회. 'reg'=규칙 진행, None=제외."""
    if not _excluded(cho, jung, jong):
        return "reg"
    return irregular.kind(word)


def _drop_jong(stem):                              # 마지막 받침 제거 (춥→추)
    cho, jung, _ = _dec(stem[-1])
    return stem[:-1] + _comp(cho, jung, 0)


def _to_rieul(stem):                               # 마지막 받침 ㄷ→ㄹ (걷→걸)
    cho, jung, _ = _dec(stem[-1])
    return stem[:-1] + _comp(cho, jung, 8)


def _ah_uh(base):                                  # 모음조화로 아/어
    return base + ("아" if _dec(base[-1])[1] in (0, 8) else "어")


def _irr_stem_form(stem, k):
    """불규칙 어간의 아/어형. 르는 여기서, 나머지는 받침 변형 후 결합."""
    if k in ("ㅂ", "ㅂ와"):
        return _drop_jong(stem) + ("와" if k == "ㅂ와" else "워")
    if k == "ㅅ":
        return _ah_uh(_drop_jong(stem))
    if k == "ㄷ":
        return _ah_uh(_to_rieul(stem))
    if k == "ㅎ":                                   # ㅎ탈락 + 모음→ㅐ(ㅑ면 ㅒ): 그렇→그래
        b = _drop_jong(stem)
        cho, jung, _ = _dec(b[-1])
        return b[:-1] + _comp(cho, 3 if jung == 2 else 1, 0)
    if k == "르":                                   # 르→앞음절 ㄹ받침 + 라/러: 모르→몰라
        head = stem[:-1]
        cho, jung, _ = _dec(head[-1])
        b = head[:-1] + _comp(cho, jung, 8)
        return b + ("라" if jung in (0, 8) else "러")
    return None


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
    k = _kind(word, cho, jung, jong)
    if k is None:
        return None
    if k != "reg":
        return _irr_stem_form(stem, k)

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


def _eun_form(word):
    """-(으)ㄴ 형태 (형용사 현재관형 / 동사 과거관형). 불규칙/비활용은 None."""
    if not isinstance(word, str) or not word.endswith("다") or len(word) < 2:
        return None
    stem = word[:-1]
    last = stem[-1]
    if not _hangul(last):
        return None
    cho, jung, jong = _dec(last)
    k = _kind(word, cho, jung, jong)
    if k is None:
        return None
    if k in ("ㅂ", "ㅂ와"):                          # 춥→추운, 돕→도운
        return _drop_jong(stem) + "운"
    if k == "ㅅ":                                   # 낫→나은
        return _drop_jong(stem) + "은"
    if k == "ㄷ":                                   # 걷→걸은
        return _to_rieul(stem) + "은"
    if k == "ㅎ":                                   # 그렇→그런, 빨갛→빨간
        b = _drop_jong(stem)
        cho2, jung2, _ = _dec(b[-1])
        return b[:-1] + _comp(cho2, jung2, 4)
    if jong == 8:                                  # ㄹ→ㄴ: 길→긴, 살→산
        return stem[:-1] + _comp(cho, jung, 4)
    if jong == 0:                                  # +ㄴ: 크→큰, 가→간
        return stem[:-1] + _comp(cho, jung, 4)
    return stem + "은"                              # 받침: 작→작은, 먹→먹은


def adnominal_present(word, pos):                  # EP20 관형형 현재 (동사 -는 / 형용사 -(으)ㄴ)
    if pos == "형용사":
        return _eun_form(word)
    if pos != "동사":
        return None
    if not isinstance(word, str) or not word.endswith("다") or len(word) < 2:
        return None
    stem = word[:-1]
    last = stem[-1]
    if not _hangul(last):
        return None
    cho, jung, jong = _dec(last)
    if _kind(word, cho, jung, jong) is None:       # -는은 불규칙 무관 (걷는·짓는·모르는)
        return None
    if jong == 8:                                  # ㄹ 탈락: 살→사는
        return stem[:-1] + _comp(cho, jung, 0) + "는"
    return stem + "는"


def adnominal_past(word):                          # EP21 과거관형 -(으)ㄴ (먹은·간·산)
    return _eun_form(word)


def stem(word):                                    # EP08 다-탈락 (어간)
    if not isinstance(word, str) or not word.endswith("다") or len(word) < 2:
        return None
    return word[:-1] if _hangul(word[:-1][-1]) else None


def request(word):                                 # EP16 ~아/어 주세요
    s = present_informal(word)
    return s + " 주세요" if s else None


def negation_short(word):                          # EP19 안 ~
    p = present_polite(word)
    return "안 " + p if p else None


def negation_long(word):                           # EP19 ~지 않아요 (어간+지, 불규칙 무관)
    if not isinstance(word, str) or not word.endswith("다") or len(word) < 2:
        return None
    return word[:-1] + "지 않아요" if _hangul(word[:-1][-1]) else None


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
    k = _kind(word, cho, jung, jong)
    if k is None:
        return None
    if k in ("ㅂ", "ㅂ와"):                          # 춥→추우세요, 돕→도우세요
        return _drop_jong(stem) + "우세요"
    if k == "ㅅ":                                   # 낫→나으세요
        return _drop_jong(stem) + "으세요"
    if k == "ㄷ":                                   # 걷→걸으세요
        return _to_rieul(stem) + "으세요"
    if k == "ㅎ":                                   # 그렇→그러세요
        return _drop_jong(stem) + "세요"
    if jong == 0:
        return stem + "세요"
    if jong == 8:                                  # ㄹ 탈락 (살→사세요)
        return stem[:-1] + _comp(cho, jung, 0) + "세요"
    return stem + "으세요"
