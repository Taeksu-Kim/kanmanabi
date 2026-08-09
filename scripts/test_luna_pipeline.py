"""luna 파이프라인 테스트 — 캐시 멱등 + 예문 검증 게이트 (실제 codex 호출 없음)."""
import json

import luna


def test_cache_is_idempotent(tmp_path):
    calls = {"n": 0}

    def fake_runner(prompt, model, effort):
        calls["n"] += 1
        return json.dumps({"ok": True, "prompt_len": len(prompt)})

    ck = str(tmp_path / "k.json")
    a = luna.call(prompt="hello", cache_path=ck, runner=fake_runner)
    b = luna.call(prompt="hello", cache_path=ck, runner=fake_runner)
    assert a == b
    assert calls["n"] == 1          # 두 번째는 캐시 → 재호출 없음 (토큰 0)


def test_extract_json_from_noise():
    assert luna.extract_json('前置き\n[{"a":1}]\nおわり') == [{"a": 1}]


def test_validate_example_requires_form_in_sentence():
    # 정답 형태(form)가 문장에 실제로 들어있어야 통과
    assert luna.valid_example({"form": "먹어요", "sentence_ko": "저는 밥을 먹어요."})
    assert not luna.valid_example({"form": "먹어요", "sentence_ko": "저는 학생이에요."})
    assert not luna.valid_example({"form": "먹어요", "sentence_ko": ""})


def test_validate_nuance_form():
    ok = {"prompt_ko": "저( ) 학생이에요.", "choices": ["은", "는", "이", "가"],
          "answer": "는", "explanation_ja": "主題なので는"}
    assert luna.valid_nuance(ok)
    assert not luna.valid_nuance({**ok, "answer": "을"})        # 정답이 보기에 없음
    assert not luna.valid_nuance({**ok, "prompt_ko": "저는 학생"})  # 빈칸 없음
    assert not luna.valid_nuance({**ok, "explanation_ja": ""})   # 해설 없음
