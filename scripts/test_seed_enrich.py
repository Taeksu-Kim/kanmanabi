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


def test_incremental_only_reads_target_episode(tmp_path):
    """증분 적재는 지정한 EP의 문항만 읽는다 (다른 EP를 건드리지 않기 위한 전제)."""
    import os

    import pytest

    import seed
    if not os.path.exists(seed.NUANCE_DIR):
        pytest.skip("생성 산출물(data/)이 없는 환경 — CI에서는 건너뛴다")

    all_rows = list(seed.iter_question_rows())
    ep17 = list(seed.iter_question_rows(only_eps={"EP17"}))

    assert ep17, "EP17 문항이 있어야 한다"
    assert all(q["ep_no"] == "EP17" for q in ep17)
    assert len(ep17) < len(all_rows)
    # 어휘 문항(ep_no 없음)은 EP 필터에 걸리지 않는다
    assert any(q.get("ep_no") is None for q in all_rows)


def test_seed_requires_explicit_mode():
    """모드를 안 주면 실행되지 않아야 한다 — 실수로 전체 재구축되는 것을 막는다."""
    import subprocess
    import sys
    import os

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    r = subprocess.run([sys.executable, os.path.join(root, "scripts", "seed.py")],
                       capture_output=True, text=True,
                       env={**os.environ, "DATABASE_URL": "sqlite:///:memory:"})
    assert r.returncode != 0
    assert "--episodes" in r.stderr or "--episodes" in r.stdout
