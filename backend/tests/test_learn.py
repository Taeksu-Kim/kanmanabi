"""프로필·허브 요약·EP 목록 (docs/api_contract.md §3, coordination C0001)."""


def test_me_defaults(client):
    r = client.get("/api/me").json()
    assert isinstance(r["id"], int)          # 프론트 UserProfile.id도 number
    assert r["level_band"] == 1
    assert "nickname" not in r               # B9: 표시 이름은 name 하나로 통일


def test_patch_me_level(client):
    assert client.patch("/api/me", json={"level_band": 3}).json()["level_band"] == 3
    assert client.get("/api/me").json()["level_band"] == 3


def test_patch_me_rejects_out_of_range(client):
    assert client.patch("/api/me", json={"level_band": 9}).status_code == 422


def test_summary_shape(client):
    s = client.get("/api/learn/summary").json()
    assert s["level_band"] == 1
    assert s["grammar"]["total_episodes"] == 1          # conftest 시드: EP01 하나
    assert s["grammar"]["current_episode"] == 1         # 미완료 → 첫 EP
    assert s["grammar"]["completed_episodes"] == []
    v = s["vocabulary"]
    assert v["due_count"] == 0
    assert all({"id", "word", "meaning_ja"} == set(p) for p in v["preview"])


def test_summary_tracks_due_separately(client):
    """어휘 문제를 틀리면 vocabulary.due_count만 오른다."""
    q = client.get("/api/study/next?level=1&track=vocabulary").json()["question"]
    client.post("/api/study/answer", json={"question_id": q["id"], "answer": "__WRONG__"})
    s = client.get("/api/learn/summary").json()
    assert s["vocabulary"]["due_count"] == 1
    assert s["grammar"]["due_count"] == 0


def test_episode_steps_default_false(client):
    ep = client.get("/api/episodes").json()[0]
    assert ep["steps"] == {"video": False, "point": False, "practice": False}
    assert ep["status"] == "not_started"


def test_opened_episode_becomes_the_resume_episode(client):
    """단계를 완료하지 않아도 마지막으로 연 EP는 이어하기 위치로 기억한다."""
    from app import models

    db = client.db()
    db.add(models.Episode(ep_no="EP02", title="EP02 주격 조사", order_index=2))
    db.commit()
    db.close()

    opened = client.put("/api/episodes/EP02/progress", json={"opened": True})
    assert opened.status_code == 200
    assert opened.json()["status"] == "not_started"
    grammar = client.get("/api/learn/summary").json()["grammar"]
    assert grammar["current_episode"] == 1
    assert grammar["resume_episode"] == 2

    db = client.db()
    row = db.query(models.UserEpisodeProgress).one()
    assert row.last_opened_at is not None
    db.close()


def test_partial_step_update_makes_in_progress(client):
    """보낸 단계만 갱신되고, 하나라도 켜지면 in_progress로 파생된다."""
    r = client.put("/api/episodes/EP01/progress", json={"video": True}).json()
    assert r["steps"] == {"video": True, "point": False, "practice": False}
    assert r["status"] == "in_progress"
    r = client.put("/api/episodes/EP01/progress", json={"point": True}).json()
    assert r["steps"]["video"] is True                  # 이전 단계가 보존된다
    assert r["status"] == "in_progress"


def test_all_three_steps_derive_completed(client):
    client.put("/api/episodes/EP01/progress",
               json={"video": True, "point": True, "practice": True})
    assert client.get("/api/episodes").json()[0]["status"] == "completed"
    assert client.get("/api/learn/summary").json()["grammar"]["completed_episodes"] == [1]


def test_unchecking_step_reverts_completed(client):
    client.put("/api/episodes/EP01/progress",
               json={"video": True, "point": True, "practice": True})
    r = client.put("/api/episodes/EP01/progress", json={"practice": False}).json()
    assert r["status"] == "in_progress"
    assert client.get("/api/learn/summary").json()["grammar"]["completed_episodes"] == []


def test_episode_progress_unknown_ep_404(client):
    assert client.put("/api/episodes/EP99/progress", json={"video": True}).status_code == 404


def test_used_choices_recorded(client):
    """전송하면 그대로 저장, 미전송이면 NULL(모름)."""
    from app import models
    q = client.get("/api/study/next?level=1").json()["question"]
    client.post("/api/study/answer",
                json={"question_id": q["id"], "answer": "x", "used_choices": True})
    q2 = client.get("/api/study/next?level=1").json()["question"]
    client.post("/api/study/answer", json={"question_id": q2["id"], "answer": "x"})

    # 오답이라 같은 문제가 review로 다시 나올 수 있으므로 item_id가 아니라 순서로 확인
    db = client.db()
    rows = [a.used_choices for a in db.query(models.Attempt).order_by(models.Attempt.id).all()]
    db.close()
    assert rows == [True, None]


def test_next_by_ep_no(client):
    r = client.get("/api/study/next?level=1&track=grammar&ep_no=EP01").json()
    assert r["question"]["ep_no"] == "EP01"
    assert client.get("/api/study/next?ep_no=EP99").status_code == 404


def _add_ep(client, ep_no, order):
    from app import models
    db = client.db()
    db.add(models.Episode(ep_no=ep_no, title=f"{ep_no} 제목", order_index=order))
    db.commit(); db.close()


def test_resume_is_null_without_history(client):
    assert client.get("/api/learn/summary").json()["grammar"]["resume_episode"] is None


def test_resume_moves_to_next_when_opened_episode_completed(client):
    """마지막으로 연 EP를 완료했으면 이어하기는 다음 EP를 가리킨다."""
    _add_ep(client, "EP02", 2)
    client.put("/api/episodes/EP01/progress",
               json={"video": True, "point": True, "practice": True})
    g = client.get("/api/learn/summary").json()["grammar"]
    assert g["resume_episode"] == 2
    assert g["current_episode"] == 2          # EP01이 완료라 첫 미완료도 EP02


def test_resume_stays_on_last_episode_when_all_done(client):
    """마지막 EP까지 완료하면 이어하기는 마지막 EP에 머무른다."""
    client.put("/api/episodes/EP01/progress",
               json={"video": True, "point": True, "practice": True})
    assert client.get("/api/learn/summary").json()["grammar"]["resume_episode"] == 1


def test_resume_follows_most_recently_opened(client):
    """여러 EP를 열었으면 가장 최근 것이 이어하기 위치."""
    _add_ep(client, "EP02", 2)
    client.put("/api/episodes/EP02/progress", json={"opened": True})
    client.put("/api/episodes/EP01/progress", json={"opened": True})
    assert client.get("/api/learn/summary").json()["grammar"]["resume_episode"] == 1


def test_opened_does_not_change_steps(client):
    """opened는 단계 완료값을 건드리지 않는다."""
    client.put("/api/episodes/EP01/progress", json={"video": True})
    r = client.put("/api/episodes/EP01/progress", json={"opened": True}).json()
    assert r["steps"] == {"video": True, "point": False, "practice": False}
    assert r["status"] == "in_progress"


def test_step_update_also_records_visit(client):
    """단계를 갱신하면 opened를 안 보내도 방문으로 기록된다."""
    client.put("/api/episodes/EP01/progress", json={"video": True})
    assert client.get("/api/learn/summary").json()["grammar"]["resume_episode"] == 1
