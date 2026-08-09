# API 계약 — 백엔드 회신 (프론트 요청 대응)

> FE·BE 간 새 질문과 응답은 [`coordination/README.md`](./coordination/README.md)의 프로토콜에
> 따라 별도 메시지로 남기고, 합의된 결과만 이 문서에 반영한다.

> 프론트 핸드오프(§4 "정해야 할 다음 계약")에 대한 백엔드 측 답변. **코드 실측 기준**
> (`backend/app/study.py`·`models.py`·`deps.py`). 추측 없음 — 미구현은 미구현이라 적는다.
> 문제 데이터 현황은 [`status.md`](./status.md), 모델 설계는 [`data_model.md`](./data_model.md).

## 0. 현재 실제로 존재하는 엔드포인트 (전부)

| 메서드 | 경로 | 상태 |
|---|---|---|
| GET | `/api/study/next?level=1&track=vocabulary\|grammar` | 구현됨 (`track` 생략 가능) |
| POST | `/api/study/answer` | 구현됨 |
| GET | `/api/study/due` | 구현됨 |
| GET | `/api/study/next?...&ep_no=EP01` | 구현됨 (EP별 문법 세션) |
| GET | `/api/study/due?track=` | 구현됨 (`track` 생략 시 전체) |
| GET | `/api/me` · PATCH `/api/me` | 구현됨 (B4) |
| GET | `/api/learn/summary` | 구현됨 (B5) |
| GET | `/api/episodes` · PUT `/api/episodes/{ep_no}/progress` | 구현됨 (B7+B8 단계별 진도) |
| GET | `/api/vocab?level=&q=&favorite=&cursor=&limit=` · `/api/vocab/{id}` | 구현됨 (B6) |
| PUT/DELETE | `/api/vocab/{id}/favorite` | 구현됨 (B6) |
| POST | `/api/auth/google` · `/api/auth/logout` | 구현됨 (GIS ID 토큰, client ID 설정 완료) |
| GET | `/api/health`, `/api/health/db` | 구현됨 |

P1 학습·단어장·인증 계약과 EP01~EP43 YouTube ID가 구현됐다. 현재 외부 결정 대기는 운영
배포 도메인뿐이다.

---

## 1. ✅ 블로커 2개 — 백엔드 수정 완료 (2026-08-09)

> **B1·B2·B3 반영됨.** `/next` 응답에 `track`·`ep_no`가 추가되고 `/next?track=`으로 트랙 분리가
> 가능하다. 채점은 공백 정규화 후 비교한다. **기존 필드는 그대로라 프론트 기존 코드는 안 깨진다.**
> 아래는 무엇이 왜 문제였는지의 기록.

**수정 후 실측**: level≤2 도달 가능 문항 **4,270 → 4,621 (+351)**.

### B1. 문법 문항 351개가 절대 출제되지 않음 → **수정됨(outerjoin)**

`study.py`의 신규 출제 쿼리가 `Vocab`과 **inner join** 한다:

```python
.join(models.Vocab, models.Question.vocab_id == models.Vocab.id)
.filter(models.Vocab.level_band <= level, ...)
```

`vocab_id`가 NULL인 문항은 조인에서 탈락한다. 해당 문항:

| 종류 | 문항 수 | 예 |
|---|---|---|
| 뉘앙스(luna, EP01·02·05·06·17~42) | 280 | `밥을 먹( ) 학교에 가요` |
| EP03 호격 ~아/야 | 30 | `지훈( ), 같이 가자!` |
| EP07 「の」 의 생략 | 41 | `「지훈ちゃんの携帯」は韓国語で？` |

이 351개는 특정 어휘에 매달린 문제가 아니라 EP에 붙는 문제라 `vocab_id`가 없다. 설계상
정상이고(모델 주석: "어휘문제=vocab_id / 문법문제=episode_id"), **쿼리가 그 설계를 반영하지
못한 것**이다.

### B2. 나머지 문법 문항 396개는 어휘 세션에 섞여 나옴 → **수정됨(track/ep_no + ?track=)**

조사·활용 문항은 `vocab_key`가 있어 `vocab_id`가 채워진다. 따라서 `/next`가 어휘 문제와
**구분 없이 섞어서** 반환한다. 프론트가 아는 `qtype`은 3종인데 실제 DB에는 **48종**이 있다:

```
word_to_ja, ja_to_word, hanja_to_word,          # 어휘 (프론트가 아는 것)
particle_iga, particle_neun, particle_reul, particle_ro, particle_copula,
particle_ina, particle_irang, particle_irago, vocative_aya, possessive_ui,
conjug_stem, conjug_informal, conjug_present, conjug_past, conjug_pastpast,
conjug_honorific, conjug_request, conjug_neg_an, conjug_neg_ji, conjug_eu,
conjug_adnominal, conjug_adnominal_past,
nuance_* (22종)
```

**적용된 형태** (프론트가 §5에서 예고한 `track`을 앞당겨 도입):

```jsonc
{ "mode": "new",
  "question": { "id": 203, "qtype": "particle_iga", "track": "grammar",
                "ep_no": "EP01", "prompt": "약사( )", "choices": ["이","가"], "difficulty": 1 } }
```

- `track`: `"vocabulary" | "grammar"` — `vocab_id`/`episode_id` 중 무엇에 연결됐는지로 결정
- `ep_no`: grammar일 때만. 프론트 EP 트랙 표시에 필요
- `/next`에 `track` 쿼리 파라미터를 받아 트랙별 세션 분리 (`/study?track=grammar`)

`qtype`은 프론트에서 유니온으로 좁히지 말고 **`string`으로 두고 렌더는 `choices` 유무로
분기**하기를 권한다(48종이 계속 늘어난다). 실제 렌더에 필요한 정보는 `choices`가 비었는지
여부뿐이다.

---

## 2. P0 — 기존 학습 API 확정 (질문별 답변)

### 형식 유지 가능 여부
`next`/`answer`/`due`의 **기존 필드는 그대로 유지된다.** 위 `track`·`ep_no`는 추가만 하는
변경이라 프론트 기존 코드가 깨지지 않는다.

### difficulty 범위
**1~3** (`★☆☆`~`★★★`). 실데이터 분포:

| 값 | 의미 | 주 사용처 |
|---|---|---|
| 1 | 받침으로 기계적 결정 | 조사(이/가·을/를) |
| 2 | 규칙 적용 필요 | 활용·의 생략 |
| 3 | 의미/뉘앙스 판단 | luna 뉘앙스 전체 |

주의: **뉘앙스 문항의 3은 실측 난이도가 아니라 생성 시 고정값**이다. 정답률 데이터가 쌓이기
전까지는 정렬 기준으로만 쓰고 학습자에게 별 개수로 노출하지 않기를 권한다.

### 정답 비교 규칙
**공백 정규화 후 완전일치** (B3 적용됨). 앞뒤 공백과 내부 연속공백을 무시한다:

```python
_norm(s) = " ".join(s.split())
correct = _norm(given) == _norm(q.answer)
```

정답이 `안 앉아요`·`찾아봐 주세요`·`지훈이 생일`처럼 공백을 포함하는 문항이 많아 주관식에서
공백 하나로 오답 처리되던 문제를 막는다. 한국어라 대소문자는 무의미.

**아직 없는 것**: 동의어 세트, 유사답안 허용(Phase 1). 어휘 문제는 정답이
`みせ【店】`처럼 한자 표기를 포함하므로 주관식 채점이 여전히 빡빡하다 — 프론트에서 어휘
주관식은 선택지 토글을 적극 노출하는 편이 낫다.

### next_due
**항상 존재한다.** `answer` 처리 시 카드가 없으면 생성하고 `schedule()`이 반드시 `due_at`을
채운 뒤 반환하므로 `null`이 되는 경로가 없다. ISO 8601 + timezone (`2026-08-10T00:00:00+00:00`).

### 문제 ID 타입
**정수(int)**. `question_id`도 int로 보내면 된다. 프론트 `UserProfile.id`가 `string`인데,
백엔드 `User.id`도 int라 여기도 맞춰야 한다.

### 인증 🟡 1단계 구현됨 (client_id 대기)

```jsonc
POST /api/auth/google  ← { "credential": "<Google ID 토큰>" }
{ "id": 1, "name": "…", "email": "…", "picture": "…",
  "level_band": null, "onboarded": false }     // httpOnly 세션 쿠키 Set-Cookie
POST /api/auth/logout  → { "ok": true }
```

- 프론트가 Google Identity Services로 받은 ID 토큰을 그대로 보낸다. 백엔드가 서명·`aud`·`iss`·
  만료를 검증하고 `provider_sub` 기준 upsert.
- 세션 = **httpOnly 쿠키** `kh_session`(SameSite=Lax, 기본 30일, 서명 토큰이라 sessions 테이블 없음).
- `onboarded: false` = `level_band` 미설정 → 온보딩으로 보내고 `PATCH /api/me`로 저장.

**설정 두 개가 독립이다.** 로그인 가능 여부와 로그인 강제 여부를 분리해, client_id를 넣고
로그인을 붙이는 동안에도 로컬 개발이 막히지 않게 했다.

| 환경변수 | 역할 | 로컬 | 운영 |
|---|---|---|---|
| `GOOGLE_CLIENT_ID` | 없으면 `/api/auth/google`이 **501** | 발급값 | 발급값 |
| `AUTH_REQUIRED` | true면 쿠키 없는 요청 **401**, false면 dev 스텁 폴백 | `false` | **`true`** |
| `SESSION_SECRET` | 세션 쿠키 서명 키(바뀌면 전체 로그아웃) | 기본값 | **필수 주입** |
| `COOKIE_SECURE` | https에서만 쿠키 전송 | `false` | **`true`** |

폴백은 `deps.get_current_user` 한 곳에서만 갈린다. 운영에서 `AUTH_REQUIRED=true`를 빠뜨리면
인증이 무력화되므로 배포 체크리스트에 넣을 것.

**Google Cloud 콘솔 설정**: ID 토큰 방식이라 "승인된 JavaScript 원본"만 필요하고 리디렉션 URI는
쓰지 않는다. 로컬은 `http://localhost:5173`·`http://127.0.0.1:5173`(포트까지가 origin, 둘은
서로 다른 origin으로 취급). 배포 도메인은 나중에 목록에 **추가**하면 된다.

"인증 전 학습 상태를 로그인 후 승계"는 아직 미정 — dev 유저와 실유저가 분리되므로
개발 데이터는 이어지지 않는다.

---

## 3. P1 — 구현 현황 (C0002에서 확정)

**필드 표기는 snake_case로 통일한다.** 기존 API가 전부 snake_case(`due_count`·`next_due`·
`correct_answer`)라 한 서비스 안에서 표기가 갈리지 않게 한다.

### 프로필 ✅ 구현됨 (B4)

```jsonc
GET   /api/me   → { "id": 1, "name": null, "email": "dev@local",
                    "picture": null, "level_band": 1 }
PATCH /api/me   ← { "level_band": 3 }     // name도 수정 가능. 범위 밖이면 422
```

- **B9 결정: `nickname` 컬럼을 두지 않는다.** 표시 이름은 `name` 하나. OAuth에서 그대로
  채워지고, 별명 편집 요구가 실제로 생기면 그때 추가한다. 프론트 `UserProfile.nickname` →
  `name`(`string | null`).
- 프론트의 `koreanLevel` = 백엔드 `level_band`. DB·문항 데이터가 전부 `level_band`라 이쪽으로 통일.

### 학습 허브 요약 ✅ 구현됨 (B5)

```jsonc
GET /api/learn/summary
{
  "level_band": 1,
  "vocabulary": {
    "preview": [{ "id": 1, "word": "가게", "meaning_ja": "みせ【店】" }],   // 유저 등급 앞 3건
    "due_count": 0
  },
  "grammar": {
    "current_episode": 1,        // 아직 완료 안 된 첫 EP 번호 (전부 완료면 마지막)
    "resume_episode": 17,        // 마지막으로 연 EP 기준 '이어하기'. number | null
    "total_episodes": 43,
    "completed_episodes": [],    // EP 번호 배열 ([1,2]), ep_no 문자열이 아님
    "due_count": 0
  }
}
```

**`current_episode` vs `resume_episode`** — 일부러 다른 값이다.
`current`는 "앞에서부터 첫 미완료"(빠뜨린 EP), `resume`은 "마지막으로 보던 곳".

| 상황 | current | resume |
|---|---|---|
| 기록 없음 | 1 | `null` |
| EP17만 열어봄 | 1 | 17 |
| EP17 3단계 완료 | 1 | 18 (다음 EP. 마지막 EP였으면 그대로) |

프론트 이어하기 대상은 `resume_episode ?? current_episode`.

두 `due_count`의 합이 `GET /api/study/due`(track 없음)와 같다.

**EP는 42가 아니라 43개다**(EP01~EP43). 프론트의 허브 표기와 학습 구조 문서도 43으로 수정했다.

### 단어장 ✅ 구현됨 (B6)

```jsonc
GET /api/vocab?level=1&q=&favorite=false&cursor=0&limit=50
{ "items": [{ "id": 1, "word": "가게", "pos": "명사", "level_band": 1,
              "ja": ["みせ【店】"], "hanja": null, "guide": "가게에 가다",
              "status": "not_started", "favorite": false }],
  "next_cursor": 3 }                       // null이면 마지막 페이지

GET    /api/vocab/{id}                     // 단건. 없으면 404
PUT    /api/vocab/{id}/favorite            // 멱등
DELETE /api/vocab/{id}/favorite            // 멱등
```

- **커서 페이지네이션** — `next_cursor`를 다음 요청 `cursor`로. `limit` 최대 100.
  1만 건이라 offset은 뒤로 갈수록 느려져서 쓰지 않는다.
- **`q`는 한국어·일본어·한자 모두 매칭**한다(`がっこう` → 학교). 일본인 학습자가 일본어 뜻으로
  찾는 경로가 핵심. 이를 위해 JSON 컬럼 직렬화를 `ensure_ascii=False`로 바꿨다 —
  기존엔 `\uXXXX`로 저장돼 일본어 LIKE가 걸리지 않았다.
- **`status`는 파생값**이다(저장 컬럼 아님). 그 단어에 연결된 문제의 `ReviewCard` 기준:
  카드 없음 `not_started` / `reps<2` `learning` / 그 외 `reviewing`.
- 즐겨찾기는 `vocab_favorites`(user_id, vocab_id) 테이블.

### EP 코스·단계별 완료 ✅ 구현됨 (B7+B8)

```jsonc
GET /api/episodes                      // 43건
[{ "ep_no": "EP01", "title": "…", "order_index": 1,
   "youtube_id": null, "summary": null,
   "steps": { "video": false, "point": false, "practice": false },
   "status": "not_started" }]

PUT /api/episodes/EP01/progress        // ← {"point":true} · 보낸 단계만 부분 갱신
{ "ep_no": "EP01",
  "steps": { "video": false, "point": true, "practice": false },
  "status": "in_progress" }

PUT /api/episodes/EP17/progress        // ← {"opened":true} · 단계값 불변, 방문만 기록
```

- **`youtube_id`는 EP01~EP43 전부 채워졌다.** 프론트는 privacy-enhanced YouTube 임베드를
  표시하고, 방어적으로 null일 때 준비 중 안내를 유지한다.
- `status`는 세 단계에서 파생된다. 전부 false는 `not_started`, 하나 이상 true는
  `in_progress`, 전부 true는 `completed`다.
- 프론트는 EP 상세에서 `point`를 저장하고 문법 세션 완료 시 `practice: true`를 자동 저장한다.
- `completed_at`은 DB에만 기록하고 현재 응답·화면에는 노출하지 않는다.
- **`opened: true`**(C0013)는 단계를 바꾸지 않고 `last_opened_at`만 갱신한다 — EP 상세를
  열기만 해도 이어하기 위치로 기억하기 위함. 단계를 갱신하면 `opened` 없이도 방문으로 함께
  기록된다. 마이그레이션 `9428a550ee2e`.

### EP별 문법 세션 ✅ 구현됨

```
GET /api/study/next?track=grammar&ep_no=EP01     // 해당 EP 문항만. 없는 EP는 404
```

---

## 4. 기타 회신

- **OpenAPI**: FastAPI라 서버 기동 시 `/docs`·`/openapi.json`이 자동 제공된다. 별도 작업 불필요.
  로컬: `cd backend && python -m uvicorn app.main:app --port 8000`
- **배포 전제**: 프론트 가정(S3/CloudFront, `/api/*`→EC2, SPA fallback)은
  `contexts/aws_deployment_context.md`와 일치한다. 같은 오리진 구성도 동의.
- **`used_choices`** ✅ 구현됨(B10): `POST /api/study/answer`에 `used_choices: bool`을 보내면
  `Attempt.used_choices`에 저장된다(마이그레이션 `70f59c7a0e68`). **nullable**이라 미전송은
  `NULL`로 남아 "안 열었음(false)"과 "프론트가 아직 안 보냄(null)"이 구분된다. 의미는 제출 시점의
  표시 상태가 아니라 **그 문항에서 한 번이라도 선택지를 열었는지**.
- **CORS**: 현재 미들웨어가 없다. 같은 오리진 배포면 불필요하지만 **로컬 개발(vite 5173 →
  8000)에서는 필요**하다. 프론트가 vite proxy로 우회 중이면 그대로 두자.

---

## 5. 프론트·백엔드 작업 분리와 적용 순서

### 완료

| ID | 담당 | 내용 | 상태 |
|---|---|---|---|
| B1 | 백엔드 | 신규 문항 쿼리 `join` → `outerjoin` | 완료 |
| B2 | 백엔드 | `track`·`ep_no` 응답 및 `/next?track=` | 완료 |
| B3 | 백엔드 | 채점 공백 정규화 | 완료 |
| F1 | 프론트 | `difficulty`를 `1 \| 2 \| 3`으로 확장 | 완료 |
| F2 | 프론트 | `qtype: string` 수용 및 미등록 유형의 중립 라벨·입력 안내 fallback | 완료 |
| F3 | 프론트 | 허브와 학습 구조의 전체 EP 수를 43으로 수정 | 완료 |
| F4 | 프론트 | 트랙별 `/next` 요청, 세션 경로 분리, `単語`/`文法 · EP번호` 출처 표시 | 완료 |
| F5 | 프론트 | 프로필 `id: number`, `name`, `level_band` 계약 수용 | 완료 |
| F6 | 프론트 | `/learn`을 학습 허브 요약·EP 목록 실데이터로 전환 | 완료 |
| F7 | 프론트 | 문항별 `used_choices` 누적값 전송 | 완료 |
| F8 | 프론트 | EP 문법 코스·EP별 세션 연결 | 완료 |
| F9 | 프론트 | 레벨별 단어장·검색·즐겨찾기·커서 페이지네이션 연결 | 완료 |
| F10 | 프론트 | API 401 공통 감지와 인증 필요 경로 준비 | 완료 |
| F11 | 프론트 | GIS 로그인·신규 사용자 레벨 온보딩 연결 | 완료 |
| F12 | 프론트 | EP 상세 3단계 진도·문법 연습 완료 자동 저장 | 완료 |

초기 안전 순서는 `F2 → B1 → B2 → F4`였다. 백엔드 B1·B2가 먼저 반영됐지만 기존 응답 필드를
삭제하지 않아 구 프론트는 깨지지 않았고, 현재 F2·F4까지 반영되어 계약이 다시 맞은 상태다.

### 남은 외부 데이터·배포 설정

**C0008·C0009까지 B4~B10과 대응 프론트 연동이 완료됐다.** 코드 계약상 남은 P1 의존성은 없다.

| 백엔드 | 상태 | 후속 프론트 |
|---|---|---|
| B4 `/api/me` | ✅ FE 연동 완료 | `id: number`, `name`, `level_band` 사용 |
| B5 학습 허브 요약 | ✅ FE 연동 완료 | 레벨·단어 미리보기·두 트랙 진도 실데이터 사용 |
| B7+B8 EP 목록·단계별 진도 | ✅ FE 연동 완료 | EP 상세·단계 상태·문법 연습 완료 연결 |
| B9 표시 이름 | ✅ FE 수용 완료 | 가입·프로필은 `name` 사용 |
| B10 `used_choices` | ✅ FE 연동 완료 | 한 번이라도 후보를 열었는지 전송 |
| B6 단어장 | ✅ FE 연동 완료 | 레벨·검색·즐겨찾기·커서 더보기 사용 |
| Google 로그인 | ✅ FE 연동 완료 | GIS ID 토큰·401 복구·레벨 온보딩 연결 |

`used_choices`는 제출 시점의 표시 상태가 아니라 해당 문항에서 후보를 한 번이라도 열었는지를
뜻하며, 프론트는 현재 모든 답안 제출에 boolean 값을 보낸다.

외부 후속은 운영 도메인 확정이다. 도메인이 정해지면 Google 승인 JavaScript Origin, 백엔드
`ALLOWED_ORIGINS`, `AUTH_REQUIRED`, `COOKIE_SECURE`를 함께 설정한다.
