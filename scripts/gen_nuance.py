#!/usr/bin/env python3
"""T3 뉘앙스 문제 (luna 저작) — EP별 의미/뉘앙스 문법. 로직이 원리적으로 못 만드는 유형.

흐름: 프롬프트(EP별) → luna 배치콜(캐시) → 검증(EP01만 형태게이트, 나머진 경량) →
      사람 검토 → 승인(--approve로 needs_review=False). 승인 전엔 서빙 제외.

사용:
  python scripts/gen_nuance.py --ep EP30            # 생성(needs_review=True) → 검토
  python scripts/gen_nuance.py --ep EP30 --approve  # 검토 후 승인(캐시 사용, 토큰 0)
"""
import argparse
import json
import os

import luna

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "nuance")
CACHE_DIR = os.path.join(ROOT, "data", "luna_cache")
N = 15

# EP별 스펙: 문법 설명·제약·검증기. gate="form"은 은/는·이/가 받침 형태검증.
SPECS = {
    "EP01": {
        "qtype": "nuance_particle", "gate": "form",
        "rule": "助詞「은/는」(主題・対比)と「이/가」(主語・新情報)の意味の違い",
        "constraint": ("空所は各問1つだけ。空所直前の単語にパッチムがあれば은/이、なければ는/가。"
                       "正解は必ずこの形態に合わせる。対比する場合はもう一方の助詞は書いておく"
                       "（例: 저( ) 학생이에요. 동생은 회사원이에요.）"),
        "choices_hint": "은/는/이/가",
    },
    "EP30": {
        "qtype": "nuance_go_seo", "gate": "light",
        "rule": "つなぎの語尾「-고」(単純な並列・順序)と「-아/어서」(原因・手段・先行動作)の意味の違い。両方日本語では「〜て」になり混同しやすい",
        "constraint": ("空所は各問1つだけ。動詞・形容詞の語尾部分を空所にする"
                       "（例: 밥을 먹( ) 학교에 가요.）。選択肢は「고」と「아/어서」の該当形を含める"),
        "choices_hint": "고 / 아·어서（例: 먹고 / 먹어서）",
    },
}


def build_prompt(spec):
    return (
        "あなたは日本人初級者向けの韓国語問題オーサーです。\n"
        f"{spec['rule']}を問う初級穴埋め問題を{N}問、JSON配列で作ってください。\n"
        f"【厳守ルール】{spec['constraint']}\n"
        "- 初級語彙のみ、短い自然な文。パッチムだけでは解けず、意味・文脈で選ぶ問題にする。\n"
        f"- 選択肢は {spec['choices_hint']} など2〜4個。\n"
        "- 各要素: {\"prompt_ko\"(空所は( )), \"choices\", \"answer\", "
        "\"explanation_ja\"(なぜそれか、日本語と対照して)}。\n"
        "JSON配列のみ出力。"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ep", required=True)
    ap.add_argument("--approve", action="store_true", help="검토 후 승인(needs_review=False)")
    ap.add_argument("--reject", default="", help="승인 시 제외할 번호(1-based, 쉼표)")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    reject = {int(x) for x in args.reject.split(",") if x.strip()}
    spec = SPECS[args.ep]
    cache = os.path.join(CACHE_DIR, f"nuance_{args.ep}.json")
    out = os.path.join(OUT_DIR, f"{args.ep}.json")
    validate = luna.valid_nuance if spec["gate"] == "form" else luna.valid_light

    if args.force and os.path.exists(cache):
        os.remove(cache)
    print(f"[{args.ep}] luna 저작 (캐시 {os.path.basename(cache)})...")
    res = luna.call(build_prompt(spec), cache_path=cache)
    valid = [r for r in res if validate(r)]

    os.makedirs(OUT_DIR, exist_ok=True)
    questions = [{
        "qtype": spec["qtype"], "ep_no": args.ep,
        "prompt": r["prompt_ko"], "answer": r["answer"], "choices": r["choices"],
        "difficulty": 3, "source": "authored", "level": 1,
        "explanation": r["explanation_ja"], "needs_review": not args.approve,
        "vocab_key": {"word": None, "homonym_no": None, "pos": None},
    } for i, r in enumerate(valid, 1) if i not in reject]      # 반려분 제외
    json.dump(questions, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    state = "승인(서빙됨)" if args.approve else "검토 대기(needs_review, 서빙제외)"
    print(f"검증 통과 {len(valid)}/{len(res)} → {os.path.relpath(out, ROOT)} [{state}]")
    if not args.approve:
        for i, r in enumerate(valid, 1):
            print(f"  {i}. {r['prompt_ko']}  →{r['answer']} {r['choices']}")
            print(f"     {r['explanation_ja'][:60]}")


if __name__ == "__main__":
    main()
