# korean_helper (kanmanabi)

일본인 학습자를 위한 한국어 학습 웹서비스. 기획·설계는 [`docs/`](./docs), 작업 지침은 [`CLAUDE.md`](./CLAUDE.md) 참조.

## 구조

```
backend/          FastAPI + SQLAlchemy (Python)
  app/main.py       /api/health, 학습 루프 라우터
  app/study.py      /api/study/next · /answer · /due (reps 엔진)
  app/srs.py        SM-2 라이트 스케줄
  app/models.py     8 테이블 (콘텐츠 공용 + 유저 상태)
  migrations/       Alembic
frontend/         React + Vite (→ 빌드 산출물 S3/CloudFront)
scripts/          데이터 빌드 (build_vocab / gen_questions / build_vocab_neighbors / seed)
docs/             기획·설계 문서
docker-compose.yml           base (postgres 외부 미노출)
docker-compose.override.yml  로컬 dev (postgres 127.0.0.1 노출)
```

스택: Python+FastAPI / React+Vite / PostgreSQL / Docker Compose (ARM64).

## 로컬 실행 (실스택)

**전제**: `data/` 산출물(어휘 master·이웃·문제 JSON)이 있어야 한다. 없으면 아래 "데이터 생성" 먼저.

```bash
cp .env.example .env
docker compose up -d --build                       # db + backend :8000
docker compose exec backend alembic upgrade head   # 마이그레이션 (컨테이너 내부, @db)
```

시드는 호스트에서 (data/·kr_study_material 접근 필요, db는 override로 localhost 노출):

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r backend/requirements.txt -r scripts/requirements.txt
DATABASE_URL="postgresql+psycopg://korean:change-me@localhost:5432/korean_helper" \
  python scripts/seed.py                            # vocab + episodes + questions 적재
```

확인:

```bash
curl "localhost:8000/api/study/next?level=1"
curl  localhost:8000/api/study/due
```

프론트 개발: `cd frontend && npm install && npm run dev` (`/api`는 :8000 프록시).

### 데이터 생성 (최초 1회 / 재생성)

```bash
python scripts/build_vocab.py                       # 어휘 master (외부 원본 다운로드)
python scripts/build_vocab_neighbors.py --levels 1,2,3,4,5,6   # 벡터 이웃 (임베더 GPU 필요)
python scripts/gen_questions.py --levels 1,2,3,4,5,6           # 문제 생성 (임베더 불필요)
```

> `vocab_neighbors.json`만 임베더(GPU)가 필요. 나머지는 CPU로 재생성 가능. (LLM/임베더: `contexts/`)

## 상태

- ✅ 뼈대 · 데이터 모델(8테이블) · 어휘 master(10,198) · 문제 생성(로직+벡터, 24k) · 학습 루프 API(SRS)
- ⏳ 인증(현재 dev 스텁 → Google OAuth) · 프론트 학습 화면 · 배포
- sqlite로 전 구간(마이그레이션→시드→학습루프) end-to-end 검증됨.
