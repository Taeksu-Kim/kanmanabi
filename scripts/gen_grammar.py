#!/usr/bin/env python3
"""문법 문제 생성기 (Track B, 순수 로직) — 받침 기반 조사 형태 드릴.

이/가(주격) · 은/는(주제) · 을/를(목적) · (으)로(수단·방향)의 *형태*를
한글 종성(받침)으로 결정한다. LLM은 받침을 신뢰성 있게 못 하므로(실측 65%)
이 영역은 로직 전담(100%). (으)로의 ㄹ받침 예외는 ★2 함정.

정답 판정은 우리 데이터가 아니라 유니코드 분해 → 등급별 어휘 명사에 적용.
산출: data/questions_grammar.json (seed가 어휘 문제와 함께 적재).

사용: python scripts/gen_grammar.py --dry-run [--levels 1,2]
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOCAB_JSON = os.path.join(ROOT, "data", "korean_vocab_master.json")
OUT_JSON = os.path.join(ROOT, "data", "questions_grammar.json")


def jongseong(word):
    """마지막 글자의 종성 코드(0=받침없음, 8=ㄹ). 한글 아니면 None."""
    ch = word[-1]
    if not ("가" <= ch <= "힣"):
        return None
    return (ord(ch) - 0xAC00) % 28


# qtype: (라벨, 판정함수) — 판정함수(jong) → (정답, [보기], 규칙설명JP파트)
def _iga(j):
    return ("이", ["이", "가"]) if j else ("가", ["이", "가"])

def _neun(j):
    return ("은", ["은", "는"]) if j else ("는", ["은", "는"])

def _reul(j):
    return ("을", ["을", "를"]) if j else ("를", ["을", "를"])

def _ro(j):
    # 받침 없음 또는 ㄹ받침(8) → 로, 그 외 → 으로
    return ("로", ["으로", "로"]) if (j == 0 or j == 8) else ("으로", ["으로", "로"])

PARTICLES = {
    "particle_iga": ("主格「が」", _iga),
    "particle_neun": ("主題「は」", _neun),
    "particle_reul": ("目的「を」", _reul),
    "particle_ro": ("手段・方向「で・へ」", _ro),
}


def explain(word, j, qtype, answer):
    """Japanese-first 규칙 설명."""
    if j is None:
        return None
    last = word[-1]
    if qtype == "particle_ro":
        if j == 0:
            return f"「{word}」はパッチムがないので「로」"
        if j == 8:
            return f"「{word}」はㄹパッチムなので「로」（例外！으로ではない）"
        return f"「{word}」はパッチムがあるので「으로」"
    has = "パッチムがある" if j else "パッチムがない"
    return f"「{word}」({last})は{has}ので「{answer}」"


def gen_for_word(e):
    word = e["word"]
    j = jongseong(word)
    if j is None:
        return []
    out = []
    for qtype, (role, fn) in PARTICLES.items():
        answer, choices = fn(j)
        difficulty = 2 if (qtype == "particle_ro" and j == 8) else 1  # ㄹ예외=함정
        out.append({
            "qtype": qtype, "prompt": f"{word}( )", "answer": answer, "choices": choices,
            "difficulty": difficulty, "source": "generated", "level": e["level"],
            "explanation": explain(word, j, qtype, answer),
            "vocab_key": {"word": e["word"], "homonym_no": e["homonym_no"], "pos": e["pos"]},
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--levels", default="1,2")
    args = ap.parse_args()
    levels = {int(x) for x in args.levels.split(",")}

    vocab = json.load(open(VOCAB_JSON, encoding="utf-8"))
    # 명사 위주 (조사가 자연스럽게 붙는 대상)
    nouns = [e for e in vocab if e["level"] in levels and e["pos"] == "명사" and ("가" <= e["word"][-1] <= "힣")]

    questions = []
    for e in nouns:
        questions.extend(gen_for_word(e))

    # 정답 검증 (알려진 케이스)
    known = {("학생", "particle_iga"): "이", ("가게", "particle_iga"): "가",
             ("물", "particle_ro"): "로", ("집", "particle_ro"): "으로",
             ("책", "particle_reul"): "을", ("나무", "particle_neun"): "는"}
    idx = {(q["prompt"][:-3], q["qtype"]): q["answer"] for q in questions}
    for (w, t), exp in known.items():
        got = idx.get((w, t))
        assert got == exp, f"검증실패 {w} {t}: {got} != {exp}"

    print(f"문법 문항: {len(questions)} (명사 {len(nouns)} × 4조사, 등급 {sorted(levels)})")

    if args.dry_run:
        print("\n-- 샘플 --")
        for w in ["학생", "가게", "물", "집"]:
            for q in questions:
                if q["prompt"][:-3] == w and q["qtype"] in ("particle_iga", "particle_ro"):
                    print(f"  {q['prompt']} [{q['qtype']} ★{q['difficulty']}] → {q['answer']} {q['choices']} | {q['explanation']}")
        return

    json.dump(questions, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"저장: data/questions_grammar.json ({len(questions)})")


if __name__ == "__main__":
    main()
