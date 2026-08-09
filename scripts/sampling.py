"""층화 라운드로빈 샘플러 — 적은 수(cap)로 규칙 케이스를 골고루 덮는다.

문법·활용 드릴은 EP당 ~20이면 충분(규칙은 하나, 단어만 바뀜). 랜덤 대신 stratum별
라운드로빈으로 뽑아 받침 있음/없음·(으)로 ㄹ예외·활용 유형 등을 표본에 반드시 포함한다.
"""
from collections import defaultdict


def stratified_sample(items, key_fn, cap, rng):
    groups = defaultdict(list)
    for it in items:
        groups[key_fn(it)].append(it)
    for g in groups.values():
        rng.shuffle(g)

    keys = list(groups)
    out, i = [], 0
    while len(out) < cap and any(groups.values()):
        g = groups[keys[i % len(keys)]]
        if g:
            out.append(g.pop())
        i += 1
    return out
