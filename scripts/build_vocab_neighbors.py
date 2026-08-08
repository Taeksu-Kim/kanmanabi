#!/usr/bin/env python3
"""벡터 이웃 precompute — 고유어 의미오답용 (개발 때만; prod는 결과만 조회).

임베딩: "단어 + 길잡이말" (Qwen3-Embedding-0.6B, contexts/vector_db_context.md).
같은 (등급, 품사) 풀 안에서 top-k 코사인 이웃을 뽑아 data/vocab_neighbors.json 저장.
gen_questions.py 가 이 표를 읽어 고유어 의미 오답으로 쓴다.

사용: python scripts/build_vocab_neighbors.py [--levels 1,2] [--topk 15]
"""
import argparse
import json
import os
import urllib.request
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOCAB_JSON = os.path.join(ROOT, "data", "korean_vocab_master.json")
OUT_JSON = os.path.join(ROOT, "data", "vocab_neighbors.json")
EMB = "http://10.5.0.2:8001/v1/embeddings"   # WSL: 127.0.0.1 아님


def vkey(e):
    return f"{e['word']}|{e['homonym_no']}|{e['pos']}"


def embed(texts):
    out = []
    for i in range(0, len(texts), 128):
        b = texts[i:i + 128]
        req = urllib.request.Request(EMB, data=json.dumps({"model": "qwen3-emb", "input": b}).encode(),
                                     headers={"Content-Type": "application/json"})
        out += [d["embedding"] for d in json.load(urllib.request.urlopen(req, timeout=180))["data"]]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels", default="1,2")
    ap.add_argument("--topk", type=int, default=15)
    args = ap.parse_args()
    levels = {int(x) for x in args.levels.split(",")}

    vocab = json.load(open(VOCAB_JSON, encoding="utf-8"))
    sub = [e for e in vocab if e["level"] in levels]
    print(f"임베딩 대상: {len(sub)} (등급 {sorted(levels)})")

    texts = [f"{e['word']} {e['guide'] or ''}".strip() for e in sub]
    V = np.array(embed(texts), dtype=np.float32)
    V /= (np.linalg.norm(V, axis=1, keepdims=True) + 1e-8)
    print("임베딩 shape:", V.shape)

    groups = defaultdict(list)
    for i, e in enumerate(sub):
        groups[(e["level"], e["pos"])].append(i)

    neighbors = {}
    for _, idx in groups.items():
        if len(idx) < 2:
            continue
        M = V[idx]
        sims = M @ M.T
        for a, gi in enumerate(idx):
            row = sims[a]
            order = np.argsort(-row)
            out = []
            for b in order:
                if b == a:
                    continue
                out.append({"word": sub[idx[b]]["word"], "sim": round(float(row[b]), 3)})
                if len(out) >= args.topk:
                    break
            neighbors[vkey(sub[gi])] = out

    json.dump(neighbors, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"저장: data/vocab_neighbors.json ({len(neighbors)} 단어)")
    # 샘플
    for w in ["가게", "친구", "바지"]:
        k = next((vkey(e) for e in sub if e["word"] == w), None)
        if k:
            print(f"  {w}:", [n["word"] for n in neighbors[k][:6]])


if __name__ == "__main__":
    main()
