"""Codex(gpt-5.6-luna) 호출 + 캐시 + 검증 — 문제 생성의 소프트 레이어(예문·해설).

원칙(docs/question_generation.md, contexts/codex_context.md):
- 로직이 사실(정답·받침)을 계산해 프롬프트에 주고, luna는 표현만.
- **캐시 멱등**: 같은 입력은 재호출 안 함(토큰 풀 절약). 배치콜(EP당 1회).
- **검증 게이트**: 로직이 재계산·형태포함으로 확인, 통과분만 채택.
"""
import json
import os
import re
import subprocess

MODEL = "gpt-5.6-luna"
EFFORT = "none"

_BLANK = re.compile(r"[(（]\s*[)）]")


def _form_ok(prompt, answer):
    """빈칸 앞 단어의 받침으로 은/는·이/가 형태가 정답과 일치하는지 (로직 검증)."""
    m = _BLANK.search(prompt)
    if not m:
        return False
    before = prompt[:m.start()].rstrip()
    if not before or not ("가" <= before[-1] <= "힣"):
        return False
    batchim = (ord(before[-1]) - 0xAC00) % 28 != 0
    if answer in ("은", "는"):
        return answer == ("은" if batchim else "는")
    if answer in ("이", "가"):
        return answer == ("이" if batchim else "가")
    return False


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


def valid_light(item):
    """비-particle 뉘앙스용 경량 검증(형태게이트 없음). 정답성은 사람 검토가 게이트."""
    ch = item.get("choices") or []
    prompt = item.get("prompt_ko") or item.get("prompt") or ""
    return (item.get("answer") in ch and len(ch) >= 2
            and len(_BLANK.findall(prompt)) == 1 and bool(item.get("explanation_ja")))


def valid_nuance(item):
    """뉘앙스 문제 검증: 정답이 보기에 있고, 빈칸 1개, **형태가 받침과 일치**, 해설 존재.
    의미 정답성은 로직으로 검증 불가 → 통과해도 needs_review로 취급."""
    ch = item.get("choices") or []
    prompt = item.get("prompt_ko") or item.get("prompt") or ""
    answer = item.get("answer")
    if answer not in ch or len(ch) < 2 or not item.get("explanation_ja"):
        return False
    if len(_BLANK.findall(prompt)) != 1:        # 빈칸 정확히 1개
        return False
    return _form_ok(prompt, answer)             # 받침↔형태 일치 (로직)
