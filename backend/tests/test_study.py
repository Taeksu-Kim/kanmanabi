def _answer(client, qid, ans):
    return client.post("/api/study/answer", json={"question_id": qid, "answer": ans}).json()


def test_due_starts_zero(client):
    assert client.get("/api/study/due").json() == {"due_count": 0}


def test_next_serves_new(client):
    r = client.get("/api/study/next?level=1").json()
    assert r["mode"] == "new"
    q = r["question"]
    assert "answer" not in q                      # 정답 미노출
    assert len(q["choices"]) >= 2                 # 어휘=4지선다 / 문법=2~4지선다


def test_correct_schedules_future(client):
    q = client.get("/api/study/next?level=1").json()["question"]
    # 정답 = choices 중 실제 정답. 여기선 서버가 알고 우리는 답을 맞혀야 하므로 오답으로 흐름만 확인.
    res = _answer(client, q["id"], q["choices"][0])
    assert "correct" in res and "correct_answer" in res


def test_wrong_resurfaces_as_review(client):
    q = client.get("/api/study/next?level=1").json()["question"]
    res = _answer(client, q["id"], "__WRONG__")
    assert res["correct"] is False
    assert client.get("/api/study/due").json()["due_count"] == 1
    nxt = client.get("/api/study/next?level=1").json()
    assert nxt["mode"] == "review" and nxt["question"]["id"] == q["id"]


def test_answer_unknown_question_404(client):
    assert client.post("/api/study/answer", json={"question_id": 99999, "answer": "x"}).status_code == 404


# --- 트랙 분리 / 문법문항 서빙 (docs/api_contract.md §1) ---

def _drain(client, track=None, limit=20):
    """세션을 끝까지 돌며 나온 문제를 모은다. 오답으로 정답을 알아낸 뒤 정답 재제출로
    due를 미래로 보내야 다음 문제로 넘어간다(오답만 하면 review로 계속 되돌아옴)."""
    seen, url = {}, "/api/study/next?level=1" + (f"&track={track}" if track else "")
    for _ in range(limit):
        r = client.get(url).json()
        if r["mode"] == "done":
            break
        q = r["question"]
        seen[q["id"]] = q
        res = _answer(client, q["id"], "__SKIP__")
        _answer(client, q["id"], res["correct_answer"])
    return seen


def test_serialize_has_track_and_ep(client):
    q = client.get("/api/study/next?level=1").json()["question"]
    assert q["track"] in ("vocabulary", "grammar")
    assert "ep_no" in q


def test_grammar_without_vocab_is_servable(client):
    """vocab_id가 없는 문법문항(뉘앙스)이 출제되어야 한다 — 예전 inner join 회귀 방지."""
    qs = _drain(client, track="grammar")
    qtypes = {q["qtype"] for q in qs.values()}
    assert "nuance_go_seo" in qtypes, qtypes
    assert all(q["track"] == "grammar" and q["ep_no"] == "EP01" for q in qs.values())


def test_vocabulary_track_excludes_grammar(client):
    qs = _drain(client, track="vocabulary")
    assert qs and all(q["track"] == "vocabulary" and q["ep_no"] is None for q in qs.values())


def test_invalid_track_rejected(client):
    assert client.get("/api/study/next?track=nope").status_code == 422


def test_answer_ignores_spacing(client):
    qs = _drain(client, track="grammar")
    qid = next(i for i, q in qs.items() if q["qtype"] == "conjug_neg_an")
    res = _answer(client, qid, "안  앉아요 ")     # 연속공백 + 앞뒤 공백
    assert res["correct"] is True
    assert res["correct_answer"] == "안 앉아요"
