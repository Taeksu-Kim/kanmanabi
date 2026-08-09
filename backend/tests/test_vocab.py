"""단어장 API (B6) — 목록·검색·커서·즐겨찾기·학습상태."""


def test_list_defaults(client):
    r = client.get("/api/vocab").json()
    assert {v["word"] for v in r["items"]} == {"가게", "학교"}
    assert r["next_cursor"] is None                 # 2건뿐이라 다음 페이지 없음
    assert all(v["status"] == "not_started" and v["favorite"] is False for v in r["items"])


def test_list_filters_by_level(client):
    assert len(client.get("/api/vocab?level=1").json()["items"]) == 2
    assert client.get("/api/vocab?level=6").json()["items"] == []
    assert client.get("/api/vocab?level=9").status_code == 422


def test_search_by_korean_and_japanese(client):
    """일본인 학습자가 일본어 뜻으로도 찾을 수 있어야 한다."""
    assert [v["word"] for v in client.get("/api/vocab?q=학교").json()["items"]] == ["학교"]
    assert [v["word"] for v in client.get("/api/vocab?q=がっこう").json()["items"]] == ["학교"]
    assert [v["word"] for v in client.get("/api/vocab?q=學校").json()["items"]] == ["학교"]  # 한자
    assert client.get("/api/vocab?q=존재하지않음").json()["items"] == []


def test_cursor_pagination(client):
    first = client.get("/api/vocab?limit=1").json()
    assert len(first["items"]) == 1 and first["next_cursor"] == first["items"][0]["id"]
    second = client.get(f"/api/vocab?limit=1&cursor={first['next_cursor']}").json()
    assert second["items"][0]["id"] != first["items"][0]["id"]
    assert second["next_cursor"] is None            # 마지막 페이지


def test_favorite_roundtrip(client):
    vid = client.get("/api/vocab").json()["items"][0]["id"]
    assert client.put(f"/api/vocab/{vid}/favorite").json()["favorite"] is True
    assert client.get(f"/api/vocab/{vid}").json()["favorite"] is True
    assert [v["id"] for v in client.get("/api/vocab?favorite=true").json()["items"]] == [vid]
    client.put(f"/api/vocab/{vid}/favorite")        # 중복 호출도 안전
    client.delete(f"/api/vocab/{vid}/favorite")
    assert client.get("/api/vocab?favorite=true").json()["items"] == []


def test_status_derives_from_review_cards(client):
    """단어 학습상태는 그 단어에 연결된 문제의 SRS 카드에서 파생된다."""
    q = client.get("/api/study/next?level=1&track=vocabulary").json()["question"]
    client.post("/api/study/answer", json={"question_id": q["id"], "answer": "__WRONG__"})
    statuses = {v["word"]: v["status"] for v in client.get("/api/vocab").json()["items"]}
    assert "learning" in statuses.values(), statuses


def test_detail_404(client):
    assert client.get("/api/vocab/99999").status_code == 404
    assert client.put("/api/vocab/99999/favorite").status_code == 404
