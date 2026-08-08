#!/usr/bin/env python3
"""Phase 0 로직 문제 생성기 (LLM/벡터 없음).

data/korean_vocab_master.json 에서 어휘 MCQ를 생성한다.
유형: word_to_ja(단어→뜻), ja_to_word(뜻→단어), hanja_to_word(한자→단어, 한자어만).

오답(distractor) = 같은 등급·품사 풀에서 [한자공유 + 형태유사 + 랜덤] 믹스.
가드: 동의어(ja 겹침) 제외 · 하위어(부분문자열) 제외.
설계: docs/question_generation.md.

사용:
  python scripts/gen_questions.py --dry-run [--levels 1,2]   # 미리보기·검증
  python scripts/gen_questions.py --levels 1,2               # data/questions_generated.json 생성
"""
import argparse
import json
import os
import random
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOCAB_JSON = os.path.join(ROOT, "data", "korean_vocab_master.json")
OUT_JSON = os.path.join(ROOT, "data", "questions_generated.json")


def lev(a, b):
    dp = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev = dp[0]; dp[0] = i
        for j, cb in enumerate(b, 1):
            cur = dp[j]; dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + (ca != cb)); prev = cur
    return dp[-1]


def form_sim(a, b):
    return 1 - lev(a, b) / max(len(a), len(b), 1)


def vkey(e):
    return {"word": e["word"], "homonym_no": e["homonym_no"], "pos": e["pos"]}


def pick_distractors(target, pool, rng, k=3):
    """[한자공유 + 형태유사 + 랜덤] 믹스, 가드 적용. distractor 어휘 엔트리 리스트 반환."""
    tw = target["word"]; tja = set(target["ja"]); th = set(target["hanja"] or "")

    def ok(c):
        if c["word"] == tw:
            return False
        if set(c["ja"]) & tja:            # 동의어 제외
            return False
        if tw in c["word"] or c["word"] in tw:   # 하위어/상위어 제외 (바지⊂청바지)
            return False
        return True

    cands = [c for c in pool if ok(c)]
    if not cands:
        return []

    hanja_share = [c for c in cands if th and c["hanja"] and set(c["hanja"]) & th]
    form_close = sorted((c for c in cands), key=lambda c: form_sim(tw, c["word"]), reverse=True)
    form_close = [c for c in form_close if form_sim(tw, c["word"]) >= 0.5]

    picked, seen = [], set()
    def add(lst):
        for c in lst:
            if c["word"] not in seen:
                picked.append(c); seen.add(c["word"]); return True
        return False

    add(hanja_share)                        # 의미 함정(한자어)
    add(form_close)                         # 형태 함정
    rng.shuffle(cands)
    while len(picked) < k:                  # 나머지는 같은 등급·품사 랜덤
        if not add(cands):
            break
    return picked[:k]


def gen_for_word(e, pool, rng):
    ds = pick_distractors(e, pool, rng)
    if len(ds) < 3:
        return []
    used_hanja_trap = any(e["hanja"] and d["hanja"] and set(e["hanja"]) & set(d["hanja"]) for d in ds)
    difficulty = 2 if used_hanja_trap else 1   # (벡터 도입 후 유사도 밴드로 정교화)
    out = []

    def q(qtype, prompt, answer, choices):
        opts = list(dict.fromkeys(choices + [answer]))   # 중복 제거
        if answer not in opts or len(opts) < 4:
            return
        rng.shuffle(opts)
        out.append({
            "qtype": qtype, "prompt": prompt, "answer": answer, "choices": opts,
            "difficulty": difficulty, "source": "generated", "level": e["level"],
            "vocab_key": vkey(e),
        })

    # 단어 → 뜻
    q("word_to_ja", e["word"], e["ja"][0], [d["ja"][0] for d in ds])
    # 뜻 → 단어
    q("ja_to_word", e["ja"][0], e["word"], [d["word"] for d in ds])
    # 한자 → 단어 (한자어만, 오답도 한자 보유로)
    if e["hanja"]:
        hd = [d for d in ds if d["hanja"]]
        if len(hd) >= 3:
            q("hanja_to_word", e["hanja"], e["word"], [d["word"] for d in hd])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--levels", default="1,2", help="쉼표구분 등급 (기본 초급 1,2)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    levels = {int(x) for x in args.levels.split(",")}
    rng = random.Random(args.seed)

    vocab = json.load(open(VOCAB_JSON, encoding="utf-8"))
    pools = defaultdict(list)
    for e in vocab:
        pools[(e["level"], e["pos"])].append(e)

    questions = []
    for e in vocab:
        if e["level"] in levels:
            questions.extend(gen_for_word(e, pools[(e["level"], e["pos"])], rng))

    # 검증
    from collections import Counter
    by_type = Counter(q["qtype"] for q in questions)
    for q in questions:
        assert q["answer"] in q["choices"], q
        assert len(q["choices"]) == len(set(q["choices"])) == 4, q
    print(f"생성 문항: {len(questions)}  (등급 {sorted(levels)})")
    print("유형별:", dict(by_type))

    if args.dry_run:
        print("\n-- 샘플 --")
        seen = set()
        for q in questions:
            if q["qtype"] in seen:
                continue
            seen.add(q["qtype"])
            print(f"  [{q['qtype']} ★{q['difficulty']}] 문제: {q['prompt']}")
            print(f"     보기: {q['choices']}")
            print(f"     정답: {q['answer']}")
        return

    json.dump(questions, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n저장: data/questions_generated.json ({len(questions)})")


if __name__ == "__main__":
    main()
