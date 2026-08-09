#!/usr/bin/env python3
"""콘텐츠 시드: vocab master + EP 메타 → DB.

- vocab    ← data/korean_vocab_master.json
- episodes ← kr_study_material/docs/episodes/EP*/episode.md (학습 경로 메타)

연습문제(questions)는 영상용이 러프·형식 불일치라 import하지 않는다.
웹 네이티브로 별도 설계(어휘 자동생성 + 문법 저작). 상세 docs/data_model.md.

사용:
  python scripts/seed.py --dry-run    # 파싱만, 통계·샘플 (DB 불필요)
  python scripts/seed.py              # DB 적재 (재실행 시 콘텐츠 테이블 재구축)

kr_study_material 경로: 환경변수 KR_STUDY_DIR (기본 /mnt/d/workspace/kr_study_material)
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KR_STUDY = os.environ.get("KR_STUDY_DIR", "/mnt/d/workspace/kr_study_material")
VIDEO_PLAN = os.path.join(KR_STUDY, "docs", "plan", "video_plan.md")
VOCAB_JSON = os.path.join(ROOT, "data", "korean_vocab_master.json")
QUESTIONS_JSON = os.path.join(ROOT, "data", "questions_generated.json")   # gen_questions.py (어휘)
QUESTIONS_GRAMMAR_JSON = os.path.join(ROOT, "data", "questions_grammar.json")  # gen_grammar.py (조사)
QUESTIONS_CONJUG_JSON = os.path.join(ROOT, "data", "questions_conjug.json")    # gen_conjug.py (활용)
CONJUG_EXAMPLES_JSON = os.path.join(ROOT, "data", "conjug_examples.json")      # gen_examples.py (luna 예문)
NUANCE_DIR = os.path.join(ROOT, "data", "nuance")                              # gen_nuance.py (T3, EP별 파일)


def attach_example(explanation, ex):
    """활용 예문(luna)을 해설에 덧붙인다. 순수 함수 — 테스트 대상."""
    if not ex:
        return explanation
    line = f"例: {ex['sentence_ko']}（{ex['sentence_ja']}）"
    return f"{explanation}\n{line}" if explanation else line


def load_episode_videos():
    """EP → YouTube ID. 사람이 수집한 값이라 재생성 불가 — data/ 중 유일하게 git 추적한다."""
    path = os.path.join(ROOT, "data", "episode_videos.json")
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}


def parse_all_episodes():
    """video_plan.md 표(EP | 제목 | 챕터범위 | 길이 | 상태)를 파싱 — 43편 단일 소스."""
    videos = load_episode_videos()
    eps = []
    for line in open(VIDEO_PLAN, encoding="utf-8"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and re.match(r"^EP\d+$", cells[0]):
            eps.append({
                "ep_no": cells[0],
                "title": cells[1],
                "chapter_range": cells[2] or None,
                "order_index": int(re.sub(r"\D", "", cells[0])),
                "level_band": None,   # 콘텐츠 전반 초급 — 정밀 밴드 매핑은 후속
                "youtube_id": videos.get(cells[0]),
                "summary": None,
            })
    return eps


def load_vocab_master():
    return json.load(open(VOCAB_JSON, encoding="utf-8"))


def iter_question_rows(only_eps=None):
    """생성 산출물(json)에서 문항 dict를 읽는다. only_eps 지정 시 그 EP만."""
    import glob
    examples = {}
    if os.path.exists(CONJUG_EXAMPLES_JSON):
        for r in json.load(open(CONJUG_EXAMPLES_JSON, encoding="utf-8")):
            examples[r["word"]] = r
    paths = [QUESTIONS_JSON, QUESTIONS_GRAMMAR_JSON, QUESTIONS_CONJUG_JSON]
    paths += sorted(glob.glob(os.path.join(NUANCE_DIR, "*.json")))       # T3 EP별
    for path in paths:
        if not os.path.exists(path):
            continue
        for q in json.load(open(path, encoding="utf-8")):
            if only_eps is not None and q.get("ep_no") not in only_eps:
                continue
            if q["qtype"] == "conjug_present":                            # luna 예문 붙이기
                q = {**q, "explanation": attach_example(q.get("explanation"),
                                                        examples.get(q["vocab_key"]["word"]))}
            yield q


def _question(models, q, vid, epid):
    k = q["vocab_key"]
    return models.Question(
        vocab_id=vid.get((k["word"], k["homonym_no"], k["pos"])),
        episode_id=epid.get(q.get("ep_no")),       # 문법=EP연결 / 어휘=None
        prompt=q["prompt"], answer=q["answer"], choices=q["choices"],
        difficulty=q["difficulty"], qtype=q["qtype"], source=q["source"],
        explanation=q.get("explanation"), needs_review=q.get("needs_review", False),
    )


def load_episodes(eps, episodes_meta):
    """지정한 EP만 증분 적재 — 나머지 콘텐츠와 유저 진도를 건드리지 않는다.

    전체 재구축(load_db)은 questions를 전부 지웠다 다시 넣어 id가 재발급된다.
    유저가 생긴 뒤에 그러면 ReviewCard(item_id로 questions를 가리킴)가 엉뚱한
    문항을 가리키고, UserEpisodeProgress의 FK 때문에 Episode 삭제 자체가 실패한다.
    그래서 운영에서는 이 함수를 쓴다.
    """
    sys.path.insert(0, os.path.join(ROOT, "backend"))
    from app.db import SessionLocal
    from app import models

    db = SessionLocal()
    try:
        # 1) 어휘: 없는 것만 추가 (기존 행은 그대로 두어 id를 보존)
        have = {(v.word, v.homonym_no, v.pos) for v in db.query(models.Vocab).all()}
        new_vocab = [v for v in load_vocab_master()
                     if (v["word"], v["homonym_no"], v["pos"]) not in have]
        if new_vocab:
            db.bulk_save_objects([
                models.Vocab(word=v["word"], homonym_no=v["homonym_no"], pos=v["pos"],
                             level_band=v["level"], guide=v.get("guide"),
                             ja=v["ja"], hanja=v.get("hanja")) for v in new_vocab])
            db.flush()
        print(f"  vocab: +{len(new_vocab)} (기존 {len(have)})")

        # 2) 에피소드: ep_no 기준 upsert
        meta = {e["ep_no"]: e for e in episodes_meta}
        for ep_no in eps:
            if ep_no not in meta:
                raise SystemExit(f"video_plan.md에 {ep_no} 항목이 없다")
            row = db.query(models.Episode).filter_by(ep_no=ep_no).first()
            if row is None:
                db.add(models.Episode(**meta[ep_no]))
                print(f"  episode {ep_no}: 신규")
            else:
                for f, v in meta[ep_no].items():
                    setattr(row, f, v)
                print(f"  episode {ep_no}: 갱신")
        db.flush()

        # 3) 문항: 해당 EP 것만 교체. 딸린 SRS 카드·이력도 함께 정리해
        #    사라진 문항을 가리키는 orphan이 남지 않게 한다.
        epid = {e.ep_no: e.id for e in db.query(models.Episode).all()}
        target_ids = [e_id for ep_no in eps if (e_id := epid.get(ep_no))]
        old_q = [q.id for q in db.query(models.Question)
                 .filter(models.Question.episode_id.in_(target_ids)).all()]
        if old_q:
            for model in (models.ReviewCard, models.Attempt):
                db.query(model).filter(model.item_type == "question",
                                       model.item_id.in_(old_q)).delete(synchronize_session=False)
            db.query(models.Question).filter(models.Question.id.in_(old_q)).delete(
                synchronize_session=False)
            print(f"  기존 문항 {len(old_q)}개 교체 (딸린 카드·이력 정리)")

        vid = {(v.word, v.homonym_no, v.pos): v.id for v in db.query(models.Vocab).all()}
        objs = [_question(models, q, vid, epid) for q in iter_question_rows(only_eps=set(eps))]
        if objs:
            db.bulk_save_objects(objs)
        print(f"  questions: +{len(objs)}")
        db.commit()
    finally:
        db.close()


def load_db(vocab, episodes):
    sys.path.insert(0, os.path.join(ROOT, "backend"))
    from app.db import SessionLocal
    from app import models

    db = SessionLocal()
    try:
        # 콘텐츠 테이블 재구축 (파생 데이터라 안전)
        db.query(models.Question).delete()
        db.query(models.VocabEpisode).delete()
        db.query(models.Episode).delete()
        db.query(models.Vocab).delete()
        db.flush()

        db.bulk_save_objects([
            models.Vocab(
                word=v["word"], homonym_no=v["homonym_no"], pos=v["pos"],
                level_band=v["level"], guide=v.get("guide"),
                ja=v["ja"], hanja=v.get("hanja"),
            ) for v in vocab
        ])
        db.bulk_save_objects([models.Episode(**ep) for ep in episodes])
        db.flush()

        # 생성 문제 적재. vocab_key→vocab_id, ep_no→episode_id 해석.
        vid = {(v.word, v.homonym_no, v.pos): v.id for v in db.query(models.Vocab).all()}
        epid = {e.ep_no: e.id for e in db.query(models.Episode).all()}
        objs = [_question(models, q, vid, epid) for q in iter_question_rows()]
        if objs:
            db.bulk_save_objects(objs)
            print(f"  questions: {len(objs)}")
        db.commit()
    finally:
        db.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="파싱만, DB 미접속")
    ap.add_argument("--episodes", default="",
                    help="증분 적재할 EP (예: EP44,EP45). 지정 시 나머지 콘텐츠·유저 진도는 그대로 둔다")
    ap.add_argument("--rebuild", action="store_true",
                    help="전체 재구축. 콘텐츠를 모두 지우고 다시 넣는다 — 유저 진도가 깨지므로 초기 구축에만.")
    args = ap.parse_args()

    # 데이터 파일을 읽기 전에 모드부터 확정한다 — 인자를 빠뜨렸을 때
    # FileNotFoundError가 아니라 사용법이 보여야 한다.
    if not (args.dry_run or args.episodes or args.rebuild):
        raise SystemExit(
            "--episodes EP44 (증분) 또는 --rebuild (전체 재구축) 중 하나를 지정한다.\n"
            "  전체 재구축은 questions id를 재발급해 유저 SRS 진도를 무효화하므로 초기 구축에만 쓴다.")

    vocab = load_vocab_master()
    episodes = parse_all_episodes()
    print(f"vocab: {len(vocab)}")
    print(f"episodes: {len(episodes)}")

    if args.dry_run:
        print("\n-- 샘플 EP --")
        for e in episodes[:3]:
            print(f"  {e['ep_no']} | {e['chapter_range'] or '?':<10} | {e['title'][:42]}")
        miss = [e["ep_no"] for e in episodes if not e["chapter_range"]]
        print(f"\nchapter_range 누락 EP: {miss or '없음'}")
        return

    if args.episodes:
        eps = [e.strip() for e in args.episodes.split(",") if e.strip()]
        print(f"증분 적재: {', '.join(eps)}")
        load_episodes(eps, episodes)
    elif args.rebuild:
        load_db(vocab, episodes)
    else:
        load_db(vocab, episodes)          # dry-run은 위에서 반환되므로 여기 오지 않는다
    print("DB 적재 완료.")


if __name__ == "__main__":
    main()
