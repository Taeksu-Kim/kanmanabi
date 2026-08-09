#!/usr/bin/env python3
"""문법 문제 생성기 (Track B / T1: 조사 형태, 순수 로직) — EP-scoped.

각 EP의 조사만, 레벨 1,2 명사에 적용, `episode_id`에 연결(하위 연습).
받침(한글 종성)으로 형태 결정. LLM은 받침을 못 하므로(실측 65%) 로직 전담(100%).
T2(활용)·T3(뉘앙스)는 codex luna 파이프라인에서 별도. 맵: docs/ep_grammar_map.md.

산출: data/questions_grammar.json (seed가 vocab_key→vocab_id, ep_no→episode_id 해석).
사용: python scripts/gen_grammar.py --dry-run [--levels 1,2]
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOCAB_JSON = os.path.join(ROOT, "data", "korean_vocab_master.json")
OUT_JSON = os.path.join(ROOT, "data", "questions_grammar.json")


def jongseong(word):
    ch = word[-1]
    if not ("가" <= ch <= "힣"):
        return None
    return (ord(ch) - 0xAC00) % 28   # 0=받침없음, 8=ㄹ


# 조사: qtype → (라벨JP, 판정함수 jong→(정답,[보기]))
def _pair(has, no):
    return lambda j: (has, [has, no]) if j else (no, [has, no])

PARTICLE = {
    "particle_iga":   ("主格「が」",        _pair("이", "가")),
    "particle_neun":  ("主題「は」",        _pair("은", "는")),
    "particle_reul":  ("目的「を」",        _pair("을", "를")),
    "particle_ina":   ("「~でも/~か」",     _pair("이나", "나")),
    "particle_irang": ("「~と」",           _pair("이랑", "랑")),
    "particle_irago": ("「~と(引用)」",     _pair("이라고", "라고")),
    "particle_copula": ("指定詞「です」",    _pair("이에요", "예요")),
    "particle_ro":    ("手段・方向「で・へ」", None),   # ㄹ예외 → 별도 처리
}

def _ro(j):
    return ("로", ["으로", "로"]) if (j == 0 or j == 8) else ("으로", ["으로", "로"])

# EP → 그 EP에서 다루는 조사(qtype) 목록 (T1, 노운 부착)
EP_PARTICLES = {
    "EP01": ["particle_iga", "particle_neun"],
    "EP04": ["particle_copula"],
    "EP11": ["particle_reul"],
    "EP24": ["particle_ro"],
    "EP26": ["particle_ina"],
    "EP28": ["particle_irang"],
    "EP34": ["particle_irago"],
    "EP43": ["particle_ina"],
}


def explain(word, j, qtype, answer):
    last = word[-1]
    if qtype == "particle_ro":
        if j == 0:
            return f"「{word}」はパッチムがないので「로」"
        if j == 8:
            return f"「{word}」はㄹパッチムなので「로」（例外！으로ではない）"
        return f"「{word}」はパッチムがあるので「으로」"
    has = "パッチムがある" if j else "パッチムがない"
    return f"「{word}」({last})は{has}ので「{answer}」"


def answer_for(word, qtype):
    """(정답, [보기], 난이도, 해설). 순수 로직 — 데이터 불필요, 테스트 대상."""
    j = jongseong(word)
    _, fn = PARTICLE[qtype]
    answer, choices = _ro(j) if qtype == "particle_ro" else fn(j)
    diff = 2 if (qtype == "particle_ro" and j == 8) else 1
    return answer, choices, diff, explain(word, j, qtype, answer)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--levels", default="1,2")
    args = ap.parse_args()
    levels = {int(x) for x in args.levels.split(",")}

    vocab = json.load(open(VOCAB_JSON, encoding="utf-8"))
    nouns = [e for e in vocab if e["level"] in levels and e["pos"] == "명사"
             and ("가" <= e["word"][-1] <= "힣")]

    questions = []
    for ep_no, qtypes in EP_PARTICLES.items():
        for e in nouns:
            j = jongseong(e["word"])
            if j is None:
                continue
            for qtype in qtypes:
                answer, choices, diff, expl = answer_for(e["word"], qtype)
                questions.append({
                    "qtype": qtype, "ep_no": ep_no,
                    "prompt": f"{e['word']}( )", "answer": answer, "choices": choices,
                    "difficulty": diff, "source": "generated", "level": e["level"],
                    "explanation": expl,
                    "vocab_key": {"word": e["word"], "homonym_no": e["homonym_no"], "pos": e["pos"]},
                })

    # 정답 검증 (알려진 케이스)
    idx = {(q["prompt"][:-3], q["qtype"]): q["answer"] for q in questions}
    for (w, t), exp in {("학생", "particle_iga"): "이", ("가게", "particle_iga"): "가",
                        ("물", "particle_ro"): "로", ("집", "particle_ro"): "으로",
                        ("책", "particle_reul"): "을", ("가게", "particle_copula"): "예요"}.items():
        assert idx.get((w, t)) == exp, f"검증실패 {w} {t}: {idx.get((w,t))} != {exp}"

    from collections import Counter
    print(f"문법 문항: {len(questions)} (명사 {len(nouns)}, 등급 {sorted(levels)})")
    print("EP별:", dict(Counter(q["ep_no"] for q in questions)))

    if args.dry_run:
        print("\n-- 샘플 --")
        for ep in ["EP01", "EP04", "EP11", "EP24"]:
            q = next(q for q in questions if q["ep_no"] == ep)
            print(f"  {ep} {q['prompt']} [{q['qtype']} ★{q['difficulty']}] → {q['answer']} {q['choices']} | {q['explanation']}")
        return

    json.dump(questions, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"저장: data/questions_grammar.json ({len(questions)})")


if __name__ == "__main__":
    main()
