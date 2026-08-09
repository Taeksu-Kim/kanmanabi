#!/usr/bin/env python3
"""T3 뉘앙스 문제 (luna 저작) — 은/는 vs 이/가 의미 선택 (EP01).

로직이 원리적으로 못 만드는 유형(의미·주제 판단). luna가 저작하되 **정답성은 로직 검증
불가** → 전부 needs_review=True (검토 전 서빙 제외). 배치콜 1 + 캐시 + 형태검증.

사용: python scripts/gen_nuance.py [--force]
"""
import argparse
import json
import os

import luna

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "luna_cache", "nuance_eunneun_EP01.json")
OUT = os.path.join(ROOT, "data", "questions_nuance.json")
N = 15


def build_prompt():
    return (
        "あなたは日本人初級者向けの韓国語問題オーサーです。\n"
        "助詞「은/는」(主題・対比)と「이/가」(主語・新情報)の**意味の違い**を問う初級穴埋め問題を"
        f"{N}問、JSON配列で作ってください。\n"
        "【厳守ルール】\n"
        "- 空所（ ）は**各問で必ず1つだけ**。対比を出す場合はもう一方の助詞は空所にせず書いておく"
        "（例: 저( ) 학생이에요. 동생은 회사원이에요.）。\n"
        "- 形態規則: 空所の直前の単語にパッチムがあれば 은/이、なければ 는/가。"
        "正解は必ずこの形態に合わせる（例: 바람→은, 저→는）。\n"
        "- 初級語彙のみ、短い文。パッチムだけでは解けず、文脈・意味で選ぶ問題にする。\n"
        "- 各要素: {\"prompt_ko\"(空所は1つ), \"choices\"(2〜4, 은/는/이/가), "
        "\"answer\"(形態も正しく), \"explanation_ja\"(なぜその助詞か、日本語と対照して)}。\n"
        "JSON配列のみ出力。"
    )


def to_question(r):
    return {
        "qtype": "nuance_particle", "ep_no": "EP01",
        "prompt": r["prompt_ko"], "answer": r["answer"], "choices": r["choices"],
        "difficulty": 3, "source": "authored", "level": 1,
        "explanation": r["explanation_ja"], "needs_review": True,
        "vocab_key": {"word": None, "homonym_no": None, "pos": None},  # 어휘 비종속
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if args.force and os.path.exists(CACHE):
        os.remove(CACHE)

    print(f"luna 저작 배치콜 (은/는vs이/가 {N}문)... 캐시: {os.path.basename(CACHE)}")
    res = luna.call(build_prompt(), cache_path=CACHE)
    valid = [r for r in res if luna.valid_nuance(r)]
    out = [to_question(r) for r in valid]

    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"형태검증 통과: {len(valid)}/{len(res)} (전부 needs_review=검토 전 서빙 제외)")
    for r in valid[:6]:
        print(f"  {r['prompt_ko']}  보기{r['choices']} 정답 {r['answer']}")
        print(f"    해설: {r['explanation_ja'][:50]}")


if __name__ == "__main__":
    main()
