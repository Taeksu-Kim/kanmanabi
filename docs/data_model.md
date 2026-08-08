# korean_helper — 데이터 모델 (설계안 v1)

> MVP reps 루프에 필요한 최소 엔티티. 확정되면 SQLAlchemy 모델 + Alembic 마이그레이션으로 옮긴다.
> 방향: reps 엔진(능동 풀이·즉시 채점·SRS·진도) on EP 학습경로 + 사용자 계정. 상세 [`product_plan.md`](./product_plan.md).

## 설계 원칙

- **콘텐츠(EP·문제·어휘)** = 공용 자산 (모든 유저 공유, kr_study_material·vocab master에서 반입)
- **유저 상태(진도·시도·SRS)** = 유저별 (PostgreSQL의 stateful 정체)
- SRS 대상은 **question / vocab 공통** → 단일 `review_cards`로 폴리모픽 관리(테이블 중복 회피)
- 스트릭·통계는 `attempts` 타임스탬프에서 파생 (별도 로그 테이블 X)

## ER 다이어그램

```mermaid
erDiagram
    users ||--o{ user_episode_progress : has
    users ||--o{ attempts : makes
    users ||--o{ review_cards : owns
    episodes ||--o{ questions : contains
    episodes ||--o{ user_episode_progress : tracked_in
    episodes }o--o{ vocab : appears_in

    users {
        int id PK
        string auth_provider "google"
        string provider_sub "Google sub (안정 식별자)"
        string email
        string name "nullable"
        string picture "nullable"
        int level_band "1~6, 자기선택 can-do, nullable"
        datetime created_at
    }
    episodes {
        int id PK
        string ep_no UK "EP01.."
        string title
        string chapter_range "ch2~ch3"
        int level_band
        string youtube_id "nullable"
        int order_index "학습 경로 순서"
        text summary "nullable"
    }
    questions {
        int id PK
        int episode_id FK
        text prompt
        text answer
        int difficulty "1~3 (★☆☆~★★★)"
        string qtype "fill_blank|transform|mcq|short"
        json choices "nullable, mcq용"
        text explanation "일본어 대조 해설"
        int order_index
    }
    vocab {
        int id PK
        string word
        int homonym_no "nullable"
        string pos
        int level_band "1~6"
        text guide "길잡이말"
        json ja "일본어 대역 배열"
        string hanja "nullable, 한자어만"
    }
    vocab_episodes {
        int vocab_id FK
        int episode_id FK
    }
    user_episode_progress {
        int id PK
        int user_id FK
        int episode_id FK
        string status "not_started|in_progress|completed"
        datetime completed_at "nullable"
    }
    attempts {
        int id PK
        int user_id FK
        string item_type "question|vocab"
        int item_id
        bool is_correct
        text user_answer "nullable"
        datetime created_at
    }
    review_cards {
        int id PK
        int user_id FK
        string item_type "question|vocab"
        int item_id
        float ease "기본 2.5"
        int interval_days
        datetime due_at
        int reps
        int lapses
        datetime last_reviewed_at "nullable"
    }
```

## 엔티티 노트

| 테이블 | 출처/역할 | 유니크 |
|---|---|---|
| `users` | 계정. **Google OAuth 확정** — `provider_sub`(Google `sub`)가 안정 식별자, email은 변경 가능하니 보조. `level_band`는 온보딩 자기선택(밴드↔TOPIK↔can-do) | (auth_provider, provider_sub) |
| `episodes` | 학습 경로 노드. `video_plan.md`·`episode.md`에서 반입. `order_index`가 스킬트리 순서 | ep_no |
| `questions` | **웹 네이티브 문제.** `source`로 출처 구분: `generated`(어휘 자동생성) / `authored`(문법 직접저작) / `video_ep`(영상 참고, 러프). `explanation`=일본어 대조 해설 | — |
| `vocab` | `korean_vocab_master.json`(10,198) 반입 | (word, homonym_no, pos) |
| `vocab_episodes` | 어휘↔EP 정렬("이 단어가 나온 EP"). 스키마만 준비, 채우기는 후속(grep 빌드) | (vocab_id, episode_id) |
| `user_episode_progress` | 학습 경로 진도 | (user_id, episode_id) |
| `attempts` | 풀이 이벤트 로그(불변). 채점 이력·스트릭·통계의 원천 | — |
| `review_cards` | SRS 상태(유저×아이템). **due-큐 = 일일 훅의 본체.** SM-2 계열 스케줄 | (user_id, item_type, item_id) |

## 문제(questions) 설계 방침

영상 연습문제는 EP마다 표 형식이 제각각(러프)이라 **import하지 않는다**(참고 자료로만). 웹 문제는 두 경로로 채운다:

- **generated** — `korean_vocab_master`(10,198)에서 **코드로 자동 생성**(단어↔일본어뜻·한자 MCQ 등). 저작 노동 0, 확장 무한, SRS와 직결.
- **authored** — EP 문법설명을 참고해 웹 채점용으로 **직접 저작**(빈칸·변환·MCQ 등 리치 유형).

스키마(`qtype`·`choices`·`explanation`·`source`)가 두 경로를 모두 수용. 고도화 유형(듣기 받아쓰기 등)은 Parking Lot.

## SRS (review_cards)

- 알고리즘: **SM-2 라이트** (ease/interval/due_at). 정답 시 interval↑·ease 조정, 오답 시 lapse++·interval 리셋.
- `item_type`으로 question/vocab 공통 처리. 새 아이템 학습 시 카드 생성(due=now).
- 일일 훅: `due_at <= now` 카드 수 = "오늘 복습 N장".

## 인증 (Google OAuth 확정)

- 프론트: Google Identity Services 로그인 → ID 토큰(JWT) 획득 → `/api/auth/google` 로 전송.
- 백엔드: `google-auth`로 ID 토큰 검증(aud=우리 client_id, iss=google) → `provider_sub` 기준 유저 upsert → **httpOnly 세션 쿠키** 발급(프론트·/api 동일 도메인 via CloudFront라 깔끔). 세션은 서명 쿠키/JWT로 stateless → sessions 테이블 불필요.
- 필요 셋업: Google Cloud OAuth 클라이언트(웹) 발급 → `GOOGLE_CLIENT_ID` 환경변수. (→ `todo.md`)

## 이번 범위에서 뺀 것 (defer)

- **grammar_points** — krdict 문법 등급표(336개) 기반 문법포인트 단위 엔티티. MVP는 EP+question으로 충분 → 후속.
- **level_band 참조 테이블** — 밴드↔TOPIK↔can-do는 6행 고정이라 코드 상수/설정으로. DB 테이블 불필요.
- **관심사 태그 / 동적 레벨** — Parking Lot (product_plan §8).
