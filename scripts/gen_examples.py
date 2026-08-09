#!/usr/bin/env python3
"""luna 소프트 레이어 — 활용 드릴에 자연 예문 붙이기 (배치콜 1회 + 캐시 + 검증).

로직이 정답(정중형)을 이미 안다. luna는 그 형태를 그대로 쓴 초급 예문만 생성하고,
로직이 '형태가 문장에 포함되나' 검증한다. 통과분만 data/conjug_examples.json.
캐시: data/luna_cache/conjug_ex_EP15.json (재실행 시 토큰 0).

사용: python scripts/gen_examples.py [--force]
"""
import argparse
import json
import os

import luna

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONJUG_Q = os.path.join(ROOT, "data", "questions_conjug.json")
CACHE = os.path.join(ROOT, "data", "luna_cache", "conjug_ex_EP15.json")
OUT = os.path.join(ROOT, "data", "conjug_examples.json")


def build_prompt(pairs):
    lines = "\n".join(f"{w}:{f}" for w, f in pairs)
    return (
        "あなたは日本人初級者向けの韓国語教材ライターです。\n"
        "各動詞・形容詞の『丁寧形』をそのまま必ず含む、初級語彙だけの短く自然な韓国語例文を"
        "1つずつ作ってください。難しい単語・長い文は避ける。\n"
        "出力はJSON配列のみ。各要素: "
        '{"word","form","sentence_ko"(formをそのまま含む),"sentence_ja"(和訳)}\n\n'
        f"対象（word:丁寧形）:\n{lines}"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="캐시 무시하고 재호출")
    args = ap.parse_args()

    qs = json.load(open(CONJUG_Q, encoding="utf-8"))
    pairs = [(q["vocab_key"]["word"], q["answer"]) for q in qs]
    form_of = dict(pairs)

    if args.force and os.path.exists(CACHE):
        os.remove(CACHE)
    print(f"luna 배치콜 (verbs {len(pairs)})... 캐시: {os.path.basename(CACHE)}")
    res = luna.call(build_prompt(pairs), cache_path=CACHE)

    # 검증 게이트: 형태 포함 + 로직이 아는 정답과 일치
    valid, bad = [], []
    for r in res:
        r_form = form_of.get(r.get("word"))
        r["form"] = r_form or r.get("form")   # 로직의 정답으로 고정
        (valid if (r_form and luna.valid_example(r)) else bad).append(r)

    json.dump(valid, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"검증 통과: {len(valid)}/{len(res)}  (실패 {len(bad)})")
    print("\n-- 통과 샘플 --")
    for r in valid[:6]:
        print(f"  {r['word']}({r['form']}): {r['sentence_ko']}  — {r['sentence_ja']}")
    if bad:
        print("\n-- 실패(형태 미포함) 샘플 --")
        for r in bad[:4]:
            print(f"  {r.get('word')}({r.get('form')}): {r.get('sentence_ko')}")


if __name__ == "__main__":
    main()
