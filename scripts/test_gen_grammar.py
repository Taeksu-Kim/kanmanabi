"""gen_grammar 로직 테스트 (순수 로직, 데이터 불필요). 실행: pytest scripts/test_gen_grammar.py"""
import pytest

import gen_grammar as g


def test_jongseong():
    assert g.jongseong("가게") == 0        # 받침 없음
    assert g.jongseong("학생") != 0        # 받침 있음
    assert g.jongseong("물") == 8          # ㄹ받침
    assert g.jongseong("cafe") is None     # 비한글


@pytest.mark.parametrize("word,qtype,expected", [
    ("학생", "particle_iga", "이"),   ("가게", "particle_iga", "가"),
    ("학생", "particle_neun", "은"),  ("가게", "particle_neun", "는"),
    ("책", "particle_reul", "을"),    ("가게", "particle_reul", "를"),
    ("집", "particle_ina", "이나"),   ("가게", "particle_ina", "나"),
    ("집", "particle_irang", "이랑"), ("가게", "particle_irang", "랑"),
    ("집", "particle_irago", "이라고"), ("가게", "particle_irago", "라고"),
    ("학생", "particle_copula", "이에요"), ("가게", "particle_copula", "예요"),
    # (으)로: 받침없음/ㄹ→로, 그 외→으로
    ("가게", "particle_ro", "로"),    ("물", "particle_ro", "로"),  ("집", "particle_ro", "으로"),
])
def test_particle_answer(word, qtype, expected):
    answer, choices, _, _ = g.answer_for(word, qtype)
    assert answer == expected
    assert answer in choices and len(choices) == 2


def test_ro_lexception_is_hard_and_explained():
    ans, _, diff, expl = g.answer_for("물", "particle_ro")
    assert ans == "로" and diff == 2          # ㄹ예외 = 함정
    assert "例外" in expl


def test_ep_scoping_covers_expected_particles():
    assert set(g.EP_PARTICLES["EP01"]) == {"particle_iga", "particle_neun"}
    assert g.EP_PARTICLES["EP11"] == ["particle_reul"]
    assert g.EP_PARTICLES["EP24"] == ["particle_ro"]
    # 모든 EP의 조사는 정의돼 있어야 한다
    for qts in g.EP_PARTICLES.values():
        for qt in qts:
            assert qt in g.PARTICLE


def test_vocative_aya():
    """EP03 호격: 받침 O → 아, 받침 X → 야."""
    import gen_grammar as g
    assert all(g.jongseong(n) is not None for n in g.NAMES)      # 전부 한글 이름
    expected = {"지훈": "아", "하은": "아", "민준": "아", "민수": "야", "유나": "야", "다희": "야"}
    for name, want in expected.items():
        assert name in g.NAMES
        assert ("아" if g.jongseong(name) else "야") == want, name


def test_possessive_ui_omission():
    """EP07 「の」省略: 받침 이름→이, 받침없음→그대로, 씨→그대로, 나의→내."""
    import random

    import gen_grammar as g
    items = {jp: (good, bad) for jp, good, bad, _ in g.possessive_items(random.Random(1))}
    # 오답은 항상 의를 넣은 형태
    for jp, (good, bad) in items.items():
        assert "의 " in bad or bad.startswith(("나의", "저의", "너의")), (jp, bad)
        assert "의" not in good.split()[0] or good.split()[0] in ("내", "제", "니"), (jp, good)
    # 축약형은 고정
    assert items["私の友達（タメ口）"][0] == "내 친구"
    assert items["私の誕生日（丁寧）"][0] == "제 생일"
