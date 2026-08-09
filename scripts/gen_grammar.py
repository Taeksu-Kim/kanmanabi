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
import random

from sampling import stratified_sample

CAP = 20   # EP·조사별 문제 수 상한 (규칙 반복이라 소량으로 충분; docs/question_generation.md §7.5)
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


# EP03 호격 ~아/야 — 사람 이름 전용이라 어휘 마스터에 없다(고유명사). 받침 섞어 직접 둔다.
NAMES = [
    "지훈", "성민", "도현", "재현", "유진", "수빈", "예린", "지원", "은영", "하은",
    "민준", "서현", "진영", "동혁", "상원",                    # 받침 O → 아
    "민수", "지수", "지호", "수지", "유나", "미나", "나리", "소라",
    "유리", "태호", "은비", "다희", "보라", "채아", "세미",     # 받침 X → 야
]


# EP07 「の」= 의 생략 — 자연스러운 쪽 vs 의를 넣은 부자연스러운 쪽. 소유 대상 명사.
POSSESSED = [("생일", "誕生日"), ("핸드폰", "携帯"), ("가방", "カバン"), ("친구", "友達"),
             ("집", "家"), ("책", "本"), ("동생", "弟・妹"), ("학교", "学校")]


def possessive_items(rng):
    """(질문JP, 정답, 오답, 해설) — 이름+이 / 그대로 / 씨 / 내·제·니."""
    out = []
    for name in NAMES:
        noun, noun_jp = rng.choice(POSSESSED)
        if jongseong(name):                                  # 받침 O → 이름+이
            good, why = f"{name}이 {noun}", f"「{name}」はパッチムがあるので이をつけて滑らかにつなぐ。의は使わない"
        else:                                                # 받침 X → 그대로 나열
            good, why = f"{name} {noun}", f"「{name}」はパッチムがないのでそのまま並べる。의は使わない"
        out.append((f"{name}ちゃんの{noun_jp}", good, f"{name}의 {noun}", why))
    for name in NAMES[:6]:                                   # ~씨가 붙으면 그대로
        noun, noun_jp = rng.choice(POSSESSED)
        out.append((f"{name}さんの{noun_jp}", f"{name}씨 {noun}", f"{name}씨의 {noun}",
                    "「씨」がつく場合はそのまま並べる。이も의もつけない"))
    for jp, good, bad, why in [                              # 나의/저의/너의는 축약형
        ("私の友達（タメ口）", "내 친구", "나의 친구", "「나의」は縮めて「내」"),
        ("私の誕生日（丁寧）", "제 생일", "저의 생일", "「저의」は縮めて「제」"),
        ("君の携帯", "니 핸드폰", "너의 핸드폰", "「너의」は縮めて「니」"),
        ("私のカバン（丁寧）", "제 가방", "저의 가방", "「저의」は縮めて「제」"),
        ("私の家（タメ口）", "내 집", "나의 집", "「나의」は縮めて「내」"),
    ]:
        out.append((jp, good, bad, why))
    return out


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


def strata(word, qtype):
    """샘플링 층 — 규칙 케이스 커버용. (으)로는 ㄹ예외를 별도 층으로."""
    j = jongseong(word)
    if qtype == "particle_ro":
        return "none" if j == 0 else ("lieul" if j == 8 else "batchim")
    return "batchim" if j else "none"


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
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    levels = {int(x) for x in args.levels.split(",")}
    rng = random.Random(args.seed)

    vocab = json.load(open(VOCAB_JSON, encoding="utf-8"))
    nouns = [e for e in vocab if e["level"] in levels and e["pos"] == "명사"
             and ("가" <= e["word"][-1] <= "힣")]

    questions = []
    for ep_no, qtypes in EP_PARTICLES.items():
        for qtype in qtypes:                                # EP·조사별 CAP개, 층화 샘플
            for e in stratified_sample(nouns, lambda x: strata(x["word"], qtype), CAP, rng):
                answer, choices, diff, expl = answer_for(e["word"], qtype)
                questions.append({
                    "qtype": qtype, "ep_no": ep_no,
                    "prompt": f"{e['word']}( )", "answer": answer, "choices": choices,
                    "difficulty": diff, "source": "generated", "level": e["level"],
                    "explanation": expl,
                    "vocab_key": {"word": e["word"], "homonym_no": e["homonym_no"], "pos": e["pos"]},
                })

    for name in NAMES:                                      # EP03 호격 ~아/야 (친구·손아랫사람)
        j = jongseong(name)
        answer = "아" if j else "야"
        has = "パッチムがある" if j else "パッチムがない"
        questions.append({
            "qtype": "vocative_aya", "ep_no": "EP03",
            "prompt": f"{name}( ), 같이 가자!", "answer": answer, "choices": ["아", "야"],
            "difficulty": 1, "source": "generated", "level": 1,
            "explanation": (f"「{name}」は{has}ので「{answer}」。"
                            "呼びかけの~아/야は友達や年下にだけ使う（目上には~씨·~님）"),
            "vocab_key": {"word": None, "homonym_no": None, "pos": None},
        })

    for jp, good, bad, why in possessive_items(rng):         # EP07 「の」の省略
        questions.append({
            "qtype": "possessive_ui", "ep_no": "EP07",
            "prompt": f"「{jp}」は韓国語で？", "answer": good, "choices": [good, bad],
            "difficulty": 2, "source": "generated", "level": 1, "explanation": why,
            "vocab_key": {"word": None, "homonym_no": None, "pos": None},
        })

    # 규칙 정확성은 test_gen_grammar.py가 검증. 여기선 형태만 확인.
    for q in questions:
        assert q["answer"] in q["choices"] and len(q["choices"]) == 2

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
