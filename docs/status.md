# 진행 상태 · 재개 가이드 (핸드오프)

> "지금 어디까지, 어떻게 이어가나". 설계는 [`question_generation.md`](./question_generation.md)·[`ep_grammar_map.md`](./ep_grammar_map.md)·[`data_model.md`](./data_model.md), 큰 그림은 [`project_overview.md`](./project_overview.md).

## 완성·작동 중

- **백엔드**: FastAPI + SQLAlchemy, 학습 루프 API (`/api/study/next|answer|due`, SM-2). 모델 8테이블 + Alembic.
- **어휘**: `korean_vocab_master.json` 10,198 (등급·일본어·한자). 어휘 MCQ + 고유어 의미오답(벡터 이웃).
- **문제 생성 파이프라인** (3엔진): 로직(어휘·조사·활용) / 벡터(오답) / **luna(예문·뉘앙스, 캐시+검증+승인)**.
- **테스트**: 루트 `pytest` 한 방 163개 통과. TDD 유지.
- **API**: 학습루프 + 프로필/허브요약/EP목록/단어장(`/api/me`·`/learn/summary`·`/episodes`·`/vocab`).
- **인증**: Google 로그인 구현 (`/api/auth/google`, httpOnly 세션 쿠키 + Origin 검증). client_id 발급·설정 완료(`backend/.env`). `AUTH_REQUIRED=false`(개발)라 미로그인 요청은 dev 스텁 폴백 — 운영은 `true`. 프론트 GIS 버튼 연결 대기.
- **EP 영상**: 43편 `youtube_id` 반영 완료 (`data/episode_videos.json`).
- **FE·BE 협업**: [`coordination/README.md`](./coordination/README.md) 프로토콜. 계약 원본은 [`api_contract.md`](./api_contract.md).

## EP 커버 43/43 · 총 747문항 ✅

- **로직(토큰0)**: 조사·형태 EP01·03·04·07·11·24·26·28·34·43 (251) / 활용 EP08·09·10·12·13·14·15·16·19·20·21 (216)
- **luna+검토승인 23개** (`data/nuance/*.json`, 전부 승인 상태, 280문항):
  EP01·02·05·06·17·18·22·23·25·27·29·30·31·32·33·35·36·37·38·39·40·41·42

## 개발 워크플로 (커맨드)

> venv(`scratchpad/venv`)는 세션마다 사라진다. 스크립트만 돌릴 땐 `PYTHONPATH=scripts python3 scripts/gen_nuance.py ...` 로 시스템 파이썬 사용 가능(luna는 외부 의존 없음).

venv: `scratchpad/venv` (fastapi·sqlalchemy·alembic·openpyxl·lxml·numpy·pytest·uvicorn). 재구성 시 `backend/requirements-dev.txt` + `scripts/requirements.txt`.

```bash
# 데이터 재생성 (CPU, 토큰0)
python scripts/build_vocab.py                        # 어휘 master (최초 1회)
python scripts/gen_questions.py --levels 1,2,3,4,5,6  # 어휘 문제 (벡터 이웃 필요)
python scripts/gen_grammar.py --levels 1,2            # 조사 (EP당 20)
python scripts/gen_conjug.py  --levels 1,2            # 활용 (EP당 ~20, 10폼)
# 벡터 이웃(고유어 오답) — 임베더 GPU 필요 (contexts/vector_db_context.md)
python scripts/build_vocab_neighbors.py --levels 1,2,3,4,5,6

# DB (개발 = sqlite)
export DATABASE_URL="sqlite:///$PWD/data/dev.db"
(cd backend && alembic upgrade head)
python scripts/seed.py                                # vocab+episodes+questions 적재
python -m pytest -q                                   # 163 통과
(cd backend && python -m uvicorn app.main:app --port 8000)   # 라이브 API
```

## luna 뉘앙스 EP 추가법 (반복 패턴)

1. `scripts/gen_nuance.py` 의 `SPECS`에 EP 항목 추가 (문법 설명·제약·choices_hint·gate). 은/는·이/가류만 `gate:"form"`(받침 검증), 나머지 `"light"`.
2. 생성 → 검토:
   ```bash
   python scripts/gen_nuance.py --ep EP31          # luna 저작(캐시), needs_review, 출력 검토
   ```
3. 검토 후 승인(반려 번호 제외):
   ```bash
   python scripts/gen_nuance.py --ep EP31 --approve --reject 3,7   # 승인분만 서빙
   ```
   - luna는 미묘한 뉘앙스에서 ~20% 틀림(예: 타고/만나서). **내 검토가 게이트.** 캐시라 재실행 토큰0.

## 남은 작업

- **luna 뉘앙스**: 완료 ✅ (2026-08-09, 14개 검토·승인)
- **어휘·표현성**: 완료 ✅ (EP02·05·06·29·36·37·40, luna 검토·승인)
- **EP07**: 완료 ✅ — 제목은 "종합 연습"이지만 고유 문법포인트가 있다(**「の」= 의 생략**: 이름+이 `수민이 생일` / 받침없으면 그대로 `유나 핸드폰` / 씨 붙으면 그대로 / 나의→내·저의→제·너의→니). `gen_grammar.py` `possessive_items()` 로직 생성 41문항. 복습 자체는 SRS due 큐가 담당(`study.py`는 EP 필터 없음).
- **EP03(호격 -아/야)**: 완료 ✅ — 어휘 마스터에 없는 사람이름이라 `gen_grammar.py` NAMES(30개)로 로직 생성.
- **EP10(ㅡ형 활용)**: 완료 ✅ — `gen_conjug.py` FORMS에 추가(ㅡ어간만, 르 제외). 오답 = ㅡ 미탈락(쓰어요).
- **문항 수 편차 보충(보류)**: 10문항 미만 4개 EP(EP31·7 / EP27·9 / EP33·9 / EP38·10). luna 15개 생성 상한 + 반려로 얇아졌다. **지금 재생성하지 않는다** — 파이프라인이 한 번 완성된 뒤 일괄 보충 방식으로 미룸(2026-08-09 결정).
- **불규칙 활용**: lv1~2 완료 ✅ — `scripts/irregular.py` 분류표(불규칙 60 + 규칙 21). 활용 문항 188→199, 불규칙 34문항 포함. **남음**: lv3~6 후보 240개 미분류(엔진이 계속 제외) + 동음이의(묻다·굽다·이르다)·러불규칙(푸르다)은 의도적 제외.
- 스키마 등 기타: [`todo.md`](./todo.md)

## ⚠️ 유실 주의 (data/ 는 gitignore)

> `data/episode_videos.json`(EP→YouTube ID 43편)만 예외로 git 추적한다 — 사람 손 수집이라
> 재생성이 불가능하다. `.gitignore`가 `data/*` + `!data/episode_videos.json` 형태인 이유.

CPU로 재생성 가능한 건 문제없음. **토큰/검토가 든 것만 유실 주의:**
- `data/vocab_neighbors.json` — 임베더 GPU 필요 (재생성 비쌈)
- `data/luna_cache/*.json` — luna 산출 캐시 (재호출 = 토큰)
- `data/nuance/*.json` — **승인된 뉘앙스 문제 + 내 검토 결정** (유실 시 재검토)
→ 필요 시 이들만 git 예외처리로 보존 권장(`episode_videos.json`은 이미 적용).
