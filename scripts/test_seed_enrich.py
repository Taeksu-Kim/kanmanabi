"""seed.attach_example (luna 예문 → 해설 연결) 테스트."""
import seed

EX = {"sentence_ko": "저는 학교에 가요", "sentence_ja": "私は学校に行きます"}


def test_appends_example_line():
    assert seed.attach_example("「가다」→「가요」", EX) == "「가다」→「가요」\n例: 저는 학교에 가요（私は学校に行きます）"


def test_none_example_keeps_explanation():
    assert seed.attach_example("base", None) == "base"


def test_empty_explanation_uses_example_only():
    assert seed.attach_example("", EX) == "例: 저는 학교에 가요（私は学校に行きます）"


def test_episode_videos_mapping():
    """EP → YouTube ID 매핑. 사람이 수집한 값이라 재생성 불가 → 형식·누락을 지킨다."""
    import json
    import os
    import re

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    m = json.load(open(os.path.join(root, "data", "episode_videos.json"), encoding="utf-8"))

    assert sorted(m) == [f"EP{i:02d}" for i in range(1, 44)]      # EP01~EP43 빠짐없이
    assert all(re.fullmatch(r"[A-Za-z0-9_-]{11}", v) for v in m.values())
    assert len(set(m.values())) == 43                             # 중복 배정 없음
