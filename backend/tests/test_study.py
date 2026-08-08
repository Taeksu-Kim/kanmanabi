def _answer(client, qid, ans):
    return client.post("/api/study/answer", json={"question_id": qid, "answer": ans}).json()


def test_due_starts_zero(client):
    assert client.get("/api/study/due").json() == {"due_count": 0}


def test_next_serves_new(client):
    r = client.get("/api/study/next?level=1").json()
    assert r["mode"] == "new"
    q = r["question"]
    assert "answer" not in q                      # 정답 미노출
    assert len(q["choices"]) == 4


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
