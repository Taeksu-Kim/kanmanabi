# korean_helper

일본인 학습자를 위한 한국어 학습 웹서비스. 기획·설계는 [`docs/`](./docs), 작업 지침은 [`CLAUDE.md`](./CLAUDE.md) 참조.

## 구조

```
backend/          FastAPI + SQLAlchemy (Python)
  app/main.py       /api/health, /api/health/db
  app/db.py         엔진/세션 (테이블은 데이터모델 확정 후)
frontend/         React + Vite (→ 빌드 산출물 S3/CloudFront)
scripts/          데이터 빌드 (어휘 master 등 — 예정)
docker-compose.yml  backend + postgres (Postgres 외부 미노출)
docs/             기획/검증 문서
```

스택: Python+FastAPI / React+Vite / PostgreSQL / Docker Compose (ARM64).

## 로컬 실행

```bash
cp .env.example .env          # 값 채우기
docker compose up --build     # backend :8000 + postgres(내부)
curl localhost:8000/api/health      # {"status":"ok"}
curl localhost:8000/api/health/db   # {"status":"ok","db":"ok"}
```

프론트 개발:

```bash
cd frontend && npm install && npm run dev   # /api 는 :8000 으로 프록시
```

## 상태

기본 뼈대 단계 — 헬스체크만 동작. 데이터 모델·어휘 빌드·학습 기능은 미구현.
