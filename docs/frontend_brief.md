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
- **모바일 우선 반응형 웹.** 일일 복습과 짧은 학습 세션을 핵심 사용 맥락으로 삼고, 데스크톱에서도 동일한 학습 흐름을 넓고 안정적으로 제공한다.
  - 디자인 기준: 모바일 390px 우선, 430px·768px 확장 확인, 데스크톱 1280~1440px 대응.
  - 데스크톱에서도 문제 영역은 약 640~720px 안에 집중시키며, 모바일 화면을 단순 축소판으로 취급하지 않는다.
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

## 프론트엔드 기술 스택 (확정)

`frontend/`는 **React + Vite + TypeScript(strict)**와 현재 안정 버전 기반으로 전환되었다. 첫 POC 학습 루프는 `/study`에 구현되어 있으며, `src/api/client.ts`의 얇은 fetch 래퍼를 통해 실제 study API(`/next`, `/answer`, `/due`)와 연결된다. 로딩·완료·재시도·제출/다음 문제 오류 상태도 화면 안에서 처리한다.

### 런타임

- **React + Vite + TypeScript(strict)**: 앱 코어. JS 스캐폴드에서 TS 구조로 전환 완료.
- **React Router 현재 안정판 — Declarative Mode**: `BrowserRouter` 기반으로 학습·온보딩·진도·로그인 화면을 구성한다. 별도 FastAPI 백엔드와 Vite 구조를 유지하며 Framework Mode는 사용하지 않는다.
- **플레인 CSS + 디자인 토큰 + CSS Modules**:
  - 전역 토큰은 `src/styles/tokens.css`, 리셋·기본 스타일은 `src/styles/global.css`에 둔다.
  - 화면·컴포넌트 스타일은 `*.module.css`로 격리한다.
  - MUI·Chakra·shadcn 등 완성형 컴포넌트 라이브러리는 POC에서 사용하지 않는다.
  - Tailwind도 현재 규모에서는 별도 유틸리티 DSL과 설정의 이득이 작으므로 사용하지 않는다. Tailwind가 특정 외형을 강요해서가 아니라, 작은 커스텀 POC에 추가 추상화가 불필요하기 때문이다.
- **`fetch` + 얇은 API 래퍼**: `src/api/client.ts`에서 base URL, JSON 처리, `response.ok` 검사, 오류 변환을 공통 처리한다. 요청 취소가 필요한 화면에서는 `AbortController`를 사용한다.
- **Motion for React (`motion`)**: 자모 결합, 채점 피드백, 학습 카드 전환, 마스코트 반응 등 시그니처 모션에만 사용한다. 일반 버튼 hover·press는 CSS로 처리한다.
- **`lucide-react`**: 범용 UI 아이콘에 사용한다. 로고·자모 심볼·브랜드형 정답 마크는 Lucide에 의존하지 않고 직접 만든 SVG/CSS 자산을 사용한다.
- **Pretendard JP 동적 서브셋**: 일본어 UI와 한국어 학습 콘텐츠를 한 패밀리로 운영하고 WOFF2를 self-host한다. 전체 JP·KR 폰트 파일을 각각 싣지 않는다. 문서 루트는 `lang="ja"`, 한국어 단어·문장에는 `lang="ko"`를 지정한다.

Motion은 패키지명과 접근성 설정에 주의한다.

```tsx
import { MotionConfig } from "motion/react";

<MotionConfig reducedMotion="user">
  <App />
</MotionConfig>
```

`reducedMotion="user"`를 앱 루트에서 명시해야 사용자 OS의 모션 감소 설정을 따른다. 감소 설정에서는 자모·카드의 이동/레이아웃 모션을 정적 상태 또는 opacity·color 중심 피드백으로 대체한다.

### 상태·서버 데이터

- 화면 내부 UI 상태는 `useState`, 학습 세션처럼 상태 전이가 분명한 흐름은 `useReducer`를 우선한다.
- Context는 인증 사용자처럼 앱 전체에서 안정적으로 공유하는 값에만 사용한다.
- **TanStack Query는 보류**: 여러 화면에서 같은 서버 데이터를 소비하거나 캐시·재시도·백그라운드 갱신이 필요해질 때 도입한다.
- **Zustand는 보류**: 복잡한 클라이언트 전역 상태가 실제로 생길 때 도입한다.
- Redux 등 추가 상태관리 도구도 현재는 사용하지 않는다.

### API 타입 전략

현재 백엔드 study 엔드포인트는 Pydantic `response_model` 없이 딕셔너리를 반환하므로, POC에서는 `Question`, `NextResponse`, `AnswerResponse`, `DueResponse` 타입을 프론트에 명시한다. 백엔드 응답 모델이 정리되면 OpenAPI를 기준으로 타입을 자동 생성하는 방식(`openapi-typescript` 등)으로 전환한다. TypeScript 타입만으로 런타임 응답 검증이 되는 것은 아니므로 API 오류 처리는 별도로 둔다.

### 테스트·품질 도구

- **Vitest + React Testing Library + jest-dom + jsdom**: 처음부터 구성한다. 정답 제출, 다음 문제 로딩, API 오류, 문제 유형별 렌더링과 학습 세션 상태 전이를 우선 테스트한다.
- **ESLint**: TypeScript·React 규칙을 적용한다.
- **Playwright**: 브라우저 QA 런타임은 추가되었다. 390×844·1280×900 기본 반응형 검증에 이어, API 연결 빌드에서 모바일 학습 1회 흐름(`/next → /answer → /next`), 진행도 갱신, 콘솔 오류 없음과 가로 넘침 없음을 확인했다. 배포 환경이 고정되면 같은 흐름을 재사용 가능한 E2E 스위트로 커밋한다.

### 이번 POC에서 설치하지 않는 것

- TanStack Query, Zustand, Redux
- Tailwind CSS
- MUI, Chakra UI, shadcn/ui 등 컴포넌트 라이브러리
- 별도 폼 라이브러리와 런타임 스키마 라이브러리(필요가 확인되면 도입)

### 배포 조건

- Vite의 정적 빌드 결과는 기존 **S3 + CloudFront** 배포 구조와 호환한다.
- `/api/*`는 기존처럼 CloudFront에서 EC2/FastAPI origin으로 전달한다.
- `BrowserRouter`를 사용하므로 `/study` 같은 확장자 없는 프론트 경로를 직접 열거나 새로고침해도 동작하도록, CloudFront 기본 프론트 동작에 viewer-request rewrite를 설정해야 한다. 프론트 경로는 `/index.html`로 rewrite하되 `/api/*` 동작에는 이 함수를 연결하지 않는다.
- `HashRouter`는 사용하지 않는다.

권장 초기 구조:

```text
frontend/src/
  app/
    router.tsx
  api/
    client.ts
    types.ts
  features/
    study/
  components/
  styles/
    tokens.css
    global.css
  assets/
    fonts/
    mascot/
```

### 로컬 기동

- `/api` 프록시는 `frontend/vite.config.js`에 설정되어 있다.
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

## 디자인 방향 (Build Web Apps 플러그인으로 전개)

- **`build-web-apps:frontend-app-builder` 스킬을 먼저 로드**해서 팔레트·타이포·레이아웃·시그니처를 브리프에 맞게 설계한다. 구현 후에는 렌더링된 모바일·데스크톱 화면을 브라우저에서 검증한다.
- **현재는 POC.** 완성형 브랜딩·복잡한 캐릭터/일러스트에 큰 비용을 쓰지 않는다. 핵심 학습 루프의 사용성, 반복 사용감, 상태 피드백을 먼저 검증한다.
- **정서적 목표**: 심리적 거리감은 낮추되 학습한다는 느낌은 유지한다. 친근하고 부담 없으며, 짧게라도 자주 열고 싶은 경험.
- **컬러 방향**: 형광 라임이 아닌 선명한 **리프 그린**을 브랜드 중심색으로 사용한다. 밝은 중립 배경과 제한된 민트·옐로 포인트를 조합하고, 색보다 타이포·여백·상태 변화로 학습 집중도를 만든다.
  - 제안 토큰: primary `#2F8F68`, primary-strong `#207653`, mint `#E9F7EF`, ink `#19352A`, background `#F7FAF8`, surface `#FFFFFF`, border `#DCE8E1`, reward `#F4C95D`, error `#DE625C`.
  - 초록을 화면 전체에 채우지 않고 CTA·진행·선택/정답 피드백에 제한한다. 정답/오답은 색만으로 구분하지 않고 아이콘·문구를 함께 쓴다.
- ⚠️ **AI 기본 클러스터 3종 회피**: (1) 크림배경+세리프+테라코타, (2) 블랙배경+애시드그린/버밀리언 1점, (3) 신문형 헤어라인. 자유 축을 이 디폴트에 쓰지 말 것.
- **주제에서 길어올리기**: 한국어 학습(한글 자모·받침·조사), 일본인 초급자의 안심되는 톤, kanmanabi(韓+学び). 학습 카드가 첫인상 → 히어로.
- 품질 바닥: 반응형(모바일까지)·키보드 포커스 가시화·reduced-motion 존중.
- 모바일에서는 한글 IME가 열린 상태에서도 입력값과 제출 동작이 가려지지 않아야 한다. 선택지는 기본 1열, 데스크톱은 내용 길이에 따라 1~2열을 허용한다.
- 시그니처 1개에 대담함 집중, 나머진 절제.
- POC의 **주 시그니처**는 자모/음절 블록의 조립과 반응으로 만든다. 선택·정답 시 작은 이동/결합 모션만 사용하고 `prefers-reduced-motion`에서는 정적 상태로 대체한다.
- **마스코트는 보조 시그니처로 승인**: 현대 서울 패션에 한복 구조를 은근하게 섞은 20대 여성 학습 가이드. 문제 풀이 중에는 노출하지 않거나 최소화하고, 정답/오답 피드백과 세션 완료 순간에만 사용한다. 기준 시트는 [`design/concepts/mascot-character-sheet-v3.png`](./design/concepts/mascot-character-sheet-v3.png).

## 참고 문서

- [`product_plan.md`](./product_plan.md) — 페인포인트·제품 테제·타깃·지속성/레벨 방침
- [`question_generation.md`](./question_generation.md) — 문제 유형·듀얼입력·오답 설계
- [`data_model.md`](./data_model.md) — 엔티티(레벨/진도/SRS)·인증(Google OAuth 예정)
- [`../CLAUDE.md`](../CLAUDE.md) — 전체 지침·문서맵
