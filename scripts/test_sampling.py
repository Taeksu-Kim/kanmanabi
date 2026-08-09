"""층화 샘플러 테스트 (TDD). pytest scripts/test_sampling.py"""
import random

from sampling import stratified_sample


def test_respects_cap():
    items = list(range(100))
    out = stratified_sample(items, key_fn=lambda x: x % 2, cap=20, rng=random.Random(0))
    assert len(out) == 20


def test_covers_all_strata():
    # 3개 stratum이 모두 표본에 등장해야 (라운드로빈)
    items = [("a", i) for i in range(50)] + [("b", i) for i in range(50)] + [("c", i) for i in range(3)]
    out = stratified_sample(items, key_fn=lambda x: x[0], cap=9, rng=random.Random(1))
    assert {x[0] for x in out} == {"a", "b", "c"}


def test_small_pool_returns_all():
    items = [1, 2, 3]
    out = stratified_sample(items, key_fn=lambda x: 0, cap=20, rng=random.Random(2))
    assert sorted(out) == [1, 2, 3]


def test_rare_stratum_included_before_cap():
    # 희귀 stratum(1개)도 cap 안에서 반드시 포함 (예: (으)로 ㄹ예외)
    items = [("common", i) for i in range(100)] + [("rare", 0)]
    out = stratified_sample(items, key_fn=lambda x: x[0], cap=20, rng=random.Random(3))
    assert ("rare", 0) in out
