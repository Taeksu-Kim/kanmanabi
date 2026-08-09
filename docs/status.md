# 진행 상태 · 재개 가이드 (핸드오프)

> "지금 어디까지, 어떻게 이어가나". 설계는 [`question_generation.md`](./question_generation.md)·[`ep_grammar_map.md`](./ep_grammar_map.md)·[`data_model.md`](./data_model.md), 큰 그림은 [`project_overview.md`](./project_overview.md).

## 완성·작동 중

- **백엔드**: FastAPI + SQLAlchemy, 학습 루프 API (`/api/study/next|answer|due`, SM-2). 모델 8테이블 + Alembic.
- **어휘**: `korean_vocab_master.json` 10,198 (등급·일본어·한자). 어휘 MCQ + 고유어 의미오답(벡터 이웃).
- **문제 생성 파이프라인** (3엔진): 로직(어휘·조사·활용) / 벡터(오답) / **luna(예문·뉘앙스, 캐시+검증+승인)**.
- **테스트**: 루트 `pytest` 한 방 118개 통과. TDD 유지.
- **인증**: 개발 스텁 유저 (Google OAuth는 프론트 후).

## EP 커버 19/43 (문제 생성)

- **완료(로직, 토큰0)**: 조사 EP01·04·11·24·26·28·34·43 / 활용 EP08·09·12·13·14·15·16·19·20·21
- **완료(luna+검토승인)**: EP01(은/는vs이/가) · EP30(-고vs-서)
- **남음 24개**: 상세 아래 §남은 작업

## 개발 워크플로 (커맨드)

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
python -m pytest -q                                   # 118 통과
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

- **luna 뉘앙스 (14, EP당 검토)**: EP17·18·22·23·25·27·31·32·33·35·38·39·41·42
- **어휘·표현성 (7, 문법드릴 아님 → 어휘/표현 문제로)**: EP02·05·06·29·36·37·40
- **복습**: EP07 (기존 문제 묶음)
- 보류: EP03(호격 -아/야, 사람이름 전용)
- **불규칙 활용**(전 EP 공통): 엔진이 ㄷ/ㅂ/ㅅ/ㅎ/르 제외 중 → 분류데이터/luna 필요 (todo)
- 스키마 등 기타: [`todo.md`](./todo.md)

## ⚠️ 유실 주의 (data/ 는 gitignore)

CPU로 재생성 가능한 건 문제없음. **토큰/검토가 든 것만 유실 주의:**
- `data/vocab_neighbors.json` — 임베더 GPU 필요 (재생성 비쌈)
- `data/luna_cache/*.json` — luna 산출 캐시 (재호출 = 토큰)
- `data/nuance/*.json` — **승인된 뉘앙스 문제 + 내 검토 결정** (유실 시 재검토)
→ 필요 시 이들만 git 예외처리로 보존 권장.
