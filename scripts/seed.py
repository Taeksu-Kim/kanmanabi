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
QUESTIONS_JSON = os.path.join(ROOT, "data", "questions_generated.json")  # gen_questions.py 산출


def parse_all_episodes():
    """video_plan.md 표(EP | 제목 | 챕터범위 | 길이 | 상태)를 파싱 — 42편 단일 소스."""
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
                "youtube_id": None,
                "summary": None,
            })
    return eps


def load_vocab_master():
    return json.load(open(VOCAB_JSON, encoding="utf-8"))


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

        # 생성 문제 적재 (gen_questions.py 산출이 있으면). vocab_key → vocab_id 해석.
        if os.path.exists(QUESTIONS_JSON):
            vid = {(v.word, v.homonym_no, v.pos): v.id for v in db.query(models.Vocab).all()}
            qs = json.load(open(QUESTIONS_JSON, encoding="utf-8"))
            objs = []
            for q in qs:
                k = q["vocab_key"]
                objs.append(models.Question(
                    vocab_id=vid.get((k["word"], k["homonym_no"], k["pos"])),
                    prompt=q["prompt"], answer=q["answer"], choices=q["choices"],
                    difficulty=q["difficulty"], qtype=q["qtype"], source=q["source"],
                ))
            db.bulk_save_objects(objs)
            print(f"  questions: {len(objs)}")
        db.commit()
    finally:
        db.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="파싱만, DB 미접속")
    args = ap.parse_args()

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

    load_db(vocab, episodes)
    print("DB 적재 완료.")


if __name__ == "__main__":
    main()
