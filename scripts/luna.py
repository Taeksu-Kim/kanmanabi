"""Codex(gpt-5.6-luna) 호출 + 캐시 + 검증 — 문제 생성의 소프트 레이어(예문·해설).

원칙(docs/question_generation.md, contexts/codex_context.md):
- 로직이 사실(정답·받침)을 계산해 프롬프트에 주고, luna는 표현만.
- **캐시 멱등**: 같은 입력은 재호출 안 함(토큰 풀 절약). 배치콜(EP당 1회).
- **검증 게이트**: 로직이 재계산·형태포함으로 확인, 통과분만 채택.
"""
import json
import os
import subprocess

MODEL = "gpt-5.6-luna"
EFFORT = "none"


def extract_json(text):
    """codex stdout에서 JSON(배열/객체)만 추출."""
    s = text.find("[")
    o = text.find("{")
    start = min(x for x in (s, o) if x != -1)
    end = max(text.rfind("]"), text.rfind("}"))
    return json.loads(text[start:end + 1])


def _default_runner(prompt, model, effort):
    # JSON은 프롬프트 지시 + extract_json으로 받는다 (--output-schema는 API 포맷 제약이 커 미사용).
    cmd = ["codex", "exec", "-m", model, "-c", f'model_reasoning_effort="{effort}"',
           "-s", "read-only", "--skip-git-repo-check", "--ephemeral", "-C", ".", "-"]
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=600)
    return r.stdout


def call(prompt, cache_path=None, runner=_default_runner, model=MODEL, effort=EFFORT):
    """luna 호출(캐시 우선). 반환: 파싱된 JSON."""
    if cache_path and os.path.exists(cache_path):
        return json.load(open(cache_path, encoding="utf-8"))

    out = runner(prompt, model, effort)
    data = out if isinstance(out, (dict, list)) else extract_json(out)
    if cache_path:
        os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
        json.dump(data, open(cache_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return data


def valid_example(item):
    """예문 검증: 정답 형태(form)가 문장에 실제로 포함돼야 함."""
    form = (item.get("form") or "").strip()
    sent = item.get("sentence_ko") or ""
    return bool(form) and form in sent


def valid_nuance(item):
    """뉘앙스 문제 형태 검증. 정답성(의미)은 로직으로 검증 불가 → needs_review로 취급."""
    ch = item.get("choices") or []
    prompt = item.get("prompt_ko") or item.get("prompt") or ""
    return item.get("answer") in ch and len(ch) >= 2 and "(" in prompt and bool(item.get("explanation_ja"))
