#!/usr/bin/env python3
"""활용 문제 생성기 (Track B / T2, 로직 엔진) — 반말·정중·과거·경어를 EP별 생성.

conjug 엔진으로 정답 계산(불규칙은 None → 제외). EP당 CAP개 층화 샘플.
오답 = 흔한 실수(모음조화 flip / 으 토글). 레벨 1,2 동사·형용사.
불규칙·예문(luna)은 후속. 맵: docs/ep_grammar_map.md.

사용: python scripts/gen_conjug.py --dry-run [--levels 1,2]
"""
import argparse
import json
import os
import random

import conjug as c
from sampling import stratified_sample

CAP = 20
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOCAB_JSON = os.path.join(ROOT, "data", "korean_vocab_master.json")
OUT_JSON = os.path.join(ROOT, "data", "questions_conjug.json")

# (EP, key, 라벨JP, 엔진함수(entry→답)). key "present"만 qtype conjug_present (예문 연결).
FORMS = [
    ("EP08", "stem", "語幹(다抜き)", lambda e: c.stem(e["word"])),
    ("EP09", "informal", "パンマル(반말)", lambda e: c.present_informal(e["word"])),
    ("EP15", "present", "丁寧形", lambda e: c.present_polite(e["word"])),
    ("EP13", "past", "過去形", lambda e: c.past_polite(e["word"])),
    ("EP14", "pastpast", "大過去", lambda e: c.past_past_polite(e["word"])),
    ("EP12", "honorific", "敬語(〜세요)", lambda e: c.honorific(e["word"]) if e["pos"] == "동사" else None),
    ("EP16", "request", "〜てください", lambda e: c.request(e["word"]) if e["pos"] == "동사" else None),
    ("EP19", "neg_an", "否定(안)", lambda e: c.negation_short(e["word"])),
    ("EP19", "neg_ji", "否定(-지 않다)", lambda e: c.negation_long(e["word"])),
    ("EP20", "adnominal", "連体形(現在)", lambda e: c.adnominal_present(e["word"], e["pos"])),
    ("EP21", "adnominal_past", "連体形(過去)", lambda e: c.adnominal_past(e["word"]) if e["pos"] == "동사" else None),
]


def cstrata(word):
    last = word[:-1][-1]
    _, j, jo = c._dec(last)
    if last == "하":
        return "ha"
    if jo != 0:
        return "batchim"
    if j == 18:
        return "eu"
    return "contract"


def _flip(s):
    """마지막 ㅏ/ㅓ 음절 뒤집기 (모음조화 오답)."""
    for i in range(len(s) - 1, -1, -1):
        if c._hangul(s[i]):
            ch, j, jo = c._dec(s[i])
            if j == 0:
                return s[:i] + c._comp(ch, 4, jo) + s[i + 1:]
            if j == 4:
                return s[:i] + c._comp(ch, 0, jo) + s[i + 1:]
    return None


def distractor(key, ans, word):
    if key == "stem":                            # 어간 vs 어형: 먹 ↔ 먹어
        return c.present_informal(word)
    if key == "honorific":                       # 으 토글: 먹으세요↔먹세요
        return ans.replace("으세요", "세요") if "으세요" in ans else ans.replace("세요", "으세요")
    if key in ("adnominal", "adnominal_past"):   # 는↔은 (현재↔과거 관형 혼동)
        if ans.endswith("는"):
            return ans[:-1] + "은"
        if ans.endswith("은"):
            return ans[:-1] + "는"
        ch, j, jo = c._dec(ans[-1])
        return ans[:-1] + c._comp(ch, j, 0) + "는" if jo == 4 else None   # 큰→크는
    return _flip(ans)


def gen(vocab, levels, rng):
    out = []
    for ep, key, label, fn in FORMS:
        cand = [e for e in vocab if e["level"] in levels and e["pos"] in ("동사", "형용사")
                and fn(e) is not None]
        for e in stratified_sample(cand, lambda x: cstrata(x["word"]), CAP, rng):
            ans = fn(e)
            wrong = distractor(key, ans, e["word"])
            if not wrong or wrong == ans:
                continue
            qtype = "conjug_present" if key == "present" else f"conjug_{key}"
            out.append({
                "qtype": qtype, "ep_no": ep,
                "prompt": f"{e['word']} → ?（{label}）", "answer": ans, "choices": [ans, wrong],
                "difficulty": 2, "source": "generated", "level": e["level"],
                "explanation": f"「{e['word']}」の{label}は「{ans}」",
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

    for q in qs:
        assert q["answer"] in q["choices"] and q["choices"][0] != q["choices"][1]
    from collections import Counter
    print(f"활용 문항: {len(qs)}  EP별: {dict(Counter(q['ep_no'] for q in qs))}")

    if args.dry_run:
        print("\n-- 샘플 (폼별) --")
        seen = set()
        for q in qs:
            if q["ep_no"] in seen:
                continue
            seen.add(q["ep_no"])
            print(f"  {q['ep_no']} {q['prompt']} → {q['answer']} {q['choices']}")
        return
    json.dump(qs, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"저장: data/questions_conjug.json ({len(qs)})")


if __name__ == "__main__":
    main()
