# 프론트엔드 작업 브리프 (핸드오프)

> **전용 프론트 세션용 참고 문서.** 이 세션(백엔드·데이터·문제생성)에서 넘긴다.
> 먼저 `frontend-design` 스킬로 디자인 방향을 잡고 → 학습 화면 구현.

## 무엇을 만드나 (첫 목표)

**학습 화면 (study loop)** — reps 엔진의 눈에 보이는 부분:
1. 문제 출제 → 2. 유저가 **탭 선택 또는 직접 입력**으로 답 → 3. 즉시 채점(정답/오답·정답·해설) → 4. 다음.
- "오늘 복습 N장"(due) 표시.
- 백엔드 API는 아래 계약대로 **이미 동작**(라이브 확인됨).

## 타깃 · 톤

- **입문~초급 일본인 학습자.** UI 카피는 **일본어**.
- **Japanese-first**: 설명·해설·피드백은 한국어를 일본어와 대조(같은 점→다른 점→함정). 상세 [`product_plan.md`](./product_plan.md) §1.
- 브랜드: **kanmanabi** (韓 + 学び) — "한국어를 배운다"는 정체성.

## API 계약 (이미 구현·동작)

베이스: 프론트는 상대경로 `/api/...` 호출 (Vite dev proxy → :8000, 배포 시 CloudFront→EC2).
인증: **현재 없음(개발 스텁 유저)**. Google OAuth는 나중(프론트 어느 정도 후) — 지금은 로그인 없이 호출됨.

| 엔드포인트 | 응답 |
|---|---|
| `GET /api/study/next?level=1` | `{mode, question}` — mode=`new`\|`review`\|`done`. question=`{id, qtype, prompt, choices[4], difficulty}` 또는 null. **정답은 안 옴(노출 방지).** |
| `POST /api/study/answer` `{question_id, answer}` | `{correct, correct_answer, explanation, next_due}` |
| `GET /api/study/due` | `{due_count}` |
| `GET /api/health` | `{status:"ok"}` |

- `qtype`: `word_to_ja`(단어→뜻) · `ja_to_word`(뜻→단어) · `hanja_to_word`(한자→단어). qtype별 질문 라벨 다르게 표시 권장:
  - word_to_ja → 「この単語の意味は？」 / ja_to_word → 「韓国語では？」 / hanja_to_word → 「この漢字の韓国語は？」
- `answer` 필드엔 **탭이면 선택한 보기 문자열, 입력이면 타이핑 문자열**을 그대로 보냄. 채점은 정답 정확일치(MVP; 동의어 세트는 후속).
- `difficulty`: 1~2 (현재 ★2 편중 — 표시만, 로직은 백엔드).

응답 예:
```json
// GET /api/study/next?level=1
{"mode":"new","question":{"id":203,"qtype":"ja_to_word","prompt":"みせ【店】",
  "choices":["가게","가격","밥","주인"],"difficulty":2}}
// POST /api/study/answer {"question_id":203,"answer":"가게"}
{"correct":true,"correct_answer":"가게","explanation":null,"next_due":"2026-08-10T..."}
```

## UX 결정 (확정)

- **듀얼 입력**: 같은 문제에 **탭 선택 버튼 + 직접 입력 필드**를 둘 다 제공, 유저가 택. (설계 근거 [`question_generation.md`](./question_generation.md) §2)
  - 탭=인식·빠름·복습 / 입력=회상·**기억에 강함**.
  - **사용 가이드 카피**(온보딩/도움말): 「しっかり覚えたい時は入力、さっと復習は選択」.
- 채점 피드백: 정답/오답 명확 + `correct_answer` + `explanation`(있으면). 오답이어도 격려 톤(죄책감 X — `product_plan.md` 지속성 방침).
- **지속성**: due-큐가 일일 훅. 스트릭·목표는 소프트·러프(요일 고정 X).

## 스택 · 로컬 기동

- **프론트**: React + Vite (이미 `frontend/`에 스캐폴드). `/api` 프록시는 `vite.config.js`에 설정됨.
  ```bash
  cd frontend && npm install && npm run dev
  ```
- **백엔드(개발)**: 이 단계는 **sqlite 로컬 서버**로 충분(docker 불필요). data/에 산출물 있어야 함.
  ```bash
  # 최초: 마이그레이션 + 시드 (repo 루트, venv)
  DATABASE_URL="sqlite:///$PWD/data/dev.db" python -m alembic -c backend/alembic.ini upgrade head  # 또는 cd backend && alembic upgrade head
  DATABASE_URL="sqlite:///$PWD/data/dev.db" python scripts/seed.py
  # 서버
  cd backend && DATABASE_URL="sqlite:///.../data/dev.db" python -m uvicorn app.main:app --port 8000
  ```
  상세·데이터 생성은 [`../README.md`](../README.md).

## 디자인 방향 (frontend-design 스킬로 전개)

- **`frontend-design` 스킬을 먼저 로드**해서 팔레트·타이포·레이아웃·시그니처를 브리프에 맞게 설계.
- ⚠️ **AI 기본 클러스터 3종 회피**: (1) 크림배경+세리프+테라코타, (2) 블랙배경+애시드그린/버밀리언 1점, (3) 신문형 헤어라인. 자유 축을 이 디폴트에 쓰지 말 것.
- **주제에서 길어올리기**: 한국어 학습(한글 자모·받침·조사), 일본인 초급자의 안심되는 톤, kanmanabi(韓+学び). 학습 카드가 첫인상 → 히어로.
- 품질 바닥: 반응형(모바일까지)·키보드 포커스 가시화·reduced-motion 존중.
- 시그니처 1개에 대담함 집중, 나머진 절제.

## 참고 문서

- [`product_plan.md`](./product_plan.md) — 페인포인트·제품 테제·타깃·지속성/레벨 방침
- [`question_generation.md`](./question_generation.md) — 문제 유형·듀얼입력·오답 설계
- [`data_model.md`](./data_model.md) — 엔티티(레벨/진도/SRS)·인증(Google OAuth 예정)
- [`../CLAUDE.md`](../CLAUDE.md) — 전체 지침·문서맵
