"""seed.attach_example (luna 예문 → 해설 연결) 테스트."""
import seed

EX = {"sentence_ko": "저는 학교에 가요", "sentence_ja": "私は学校に行きます"}


def test_appends_example_line():
    assert seed.attach_example("「가다」→「가요」", EX) == "「가다」→「가요」\n例: 저는 학교에 가요（私は学校に行きます）"


def test_none_example_keeps_explanation():
    assert seed.attach_example("base", None) == "base"


def test_empty_explanation_uses_example_only():
    assert seed.attach_example("", EX) == "例: 저는 학교에 가요（私は学校に行きます）"
