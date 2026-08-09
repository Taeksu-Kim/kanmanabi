#!/usr/bin/env python3
"""활용 문제 생성기 (Track B / T2, 로직 엔진) — 현재 정중형(-아요/어요).

conjug.present_polite로 정답 계산(불규칙은 None → 제외). EP15(현재형)에 연결.
오답 = 흔한 실수(받침: 모음조화 반대 / 무받침: 축약 안 한 형태). 레벨 1,2 동사·형용사.
불규칙·예문(luna)은 후속. 맵: docs/ep_grammar_map.md.

사용: python scripts/gen_conjug.py --dry-run [--levels 1,2]
"""
import argparse
import json
import os
import random

import conjug as c
from sampling import stratified_sample

CAP = 20   # EP당 문제 상한 (docs/question_generation.md §7.5)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOCAB_JSON = os.path.join(ROOT, "data", "korean_vocab_master.json")
OUT_JSON = os.path.join(ROOT, "data", "questions_conjug.json")
EP = "EP15"   # 현재형 정리


def cstrata(word):
    """활용 유형 층 — 받침/축약/ㅡ탈락/하 커버용."""
    last = word[:-1][-1]
    _, j, jo = c._dec(last)
    if last == "하":
        return "ha"
    if jo != 0:
        return "batchim"
    if j == 18:
        return "eu"
    return "contract"


def naive_wrong(word):
    """흔한 오답: 받침=모음조화 반대, 무받침=축약 안 한 형태."""
    stem = word[:-1]
    cho, jung, jong = c._dec(stem[-1])
    if jong != 0:
        wrong_v = c._comp(11, 4 if jung in (0, 8) else 0, 0)   # 반대 모음
        return stem + wrong_v + "요"
    v = c._comp(11, 0 if jung in (0, 8) else 4, 0)             # 축약 전 아/어
    return stem + v + "요"


def gen(vocab, levels, rng):
    reg = [e for e in vocab if e["level"] in levels and e["pos"] in ("동사", "형용사")
           and c.present_polite(e["word"]) is not None]
    out = []
    for e in stratified_sample(reg, lambda x: cstrata(x["word"]), CAP, rng):   # EP당 CAP개
        ans = c.present_polite(e["word"])
        wrong = naive_wrong(e["word"])
        if wrong == ans:
            continue
        out.append({
            "qtype": "conjug_present", "ep_no": EP,
            "prompt": f"{e['word']} → ?（丁寧形）", "answer": ans, "choices": [ans, wrong],
            "difficulty": 2, "source": "generated", "level": e["level"],
            "explanation": f"「{e['word']}」の丁寧な現在形は「{ans}」",
            "vocab_key": {"word": e["word"], "homonym_no": e["homonym_no"], "pos": e["pos"]},
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--levels", default="1,2")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    levels = {int(x) for x in args.levels.split(",")}
    vocab = json.load(open(VOCAB_JSON, encoding="utf-8"))
    qs = gen(vocab, levels, random.Random(args.seed))

    for q in qs:                                  # 자기검증
        assert q["answer"] in q["choices"] and q["choices"][0] != q["choices"][1]
    verbs = [e for e in vocab if e["level"] in levels and e["pos"] in ("동사", "형용사")]
    print(f"활용 문항: {len(qs)} (동사·형용사 {len(verbs)} 중 규칙 활용분, 등급 {sorted(levels)})")

    if args.dry_run:
        print("\n-- 샘플 --")
        for q in qs[:8]:
            print(f"  {q['prompt']} → {q['answer']} (오답 {q['choices'][1] if q['choices'][0]==q['answer'] else q['choices'][0]})")
        return
    json.dump(qs, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"저장: data/questions_conjug.json ({len(qs)})")


if __name__ == "__main__":
    main()
