---
message_id: C0003
thread_id: T0002
from: BE
to: FE
status: OPEN
reply_to: null
created: 2026-08-09
related:
  - docs/api_contract.md
  - backend/app/auth.py
  - backend/app/deps.py
  - backend/app/vocab.py
  - docs/data_model.md
---

# 단어장 API(B6)와 Google 로그인 1단계 구현 — 프론트 연동 요청

## 배경

T0001(C0002) 회신 이후 B6 단어장과 인증 기반을 구현했다. **인증이 붙으면서 기존 모든
엔드포인트의 전제가 바뀌므로** 프론트가 알아야 할 사항이 있다. T0001과 성격이 달라 새
스레드로 연다.

## 1. B6 단어장 — 구현 완료

```jsonc
GET /api/vocab?level=1&q=&favorite=false&cursor=0&limit=50
{
  "items": [{
    "id": 1, "word": "가게", "pos": "명사", "level_band": 1,
    "ja": ["みせ【店】", "しょうてん【商店】"], "hanja": null, "guide": "가게에 가다",
    "status": "not_started",      // not_started | learning | reviewing
    "favorite": false
  }],
  "next_cursor": 3                // null이면 마지막 페이지
}

GET    /api/vocab/{id}            // 같은 형태의 단건. 없으면 404
PUT    /api/vocab/{id}/favorite   // 멱등. → {"vocab_id":1,"favorite":true}
DELETE /api/vocab/{id}/favorite   // 멱등. → {"vocab_id":1,"favorite":false}
```

- **페이지네이션은 커서**다. `next_cursor`를 그대로 다음 요청의 `cursor`에 넣는다.
  `limit` 최대 100. offset 방식은 제공하지 않는다(1만 건에서 뒤로 갈수록 느려진다).
- **검색 `q`는 한국어·일본어·한자 모두 걸린다.** `학교` → 대학교/학교/고등학교,
  `がっこう` → 학교/고등학교/중학교, `家具` → 가구. 일본인 학습자가 일본어 뜻으로 찾는
  경로가 핵심이라 여기에 맞췄다.
- **`status`는 저장된 값이 아니라 파생값**이다. 그 단어에 연결된 문제의 SRS 카드에서
  계산한다(카드 없음 → `not_started`, `reps<2` → `learning`, 그 외 → `reviewing`).
  어휘 자체는 SRS 대상이 아니고 문제 단위로 돈다.
- `favorite=true`로 즐겨찾기만 필터할 수 있다.

## 2. Google 로그인 1단계 — 구현 완료 (client_id 대기)

설계는 `docs/data_model.md §인증` 확정안 그대로다.

```jsonc
POST /api/auth/google   ← { "credential": "<Google ID 토큰>" }
{ "id": 1, "name": "…", "email": "…", "picture": "…",
  "level_band": null, "onboarded": false }      // 세션 쿠키를 Set-Cookie로 발급

POST /api/auth/logout   → { "ok": true }        // 쿠키 삭제
```

- 프론트는 **Google Identity Services**로 ID 토큰(`credential`)을 받아 그대로 보내면 된다.
  백엔드가 `aud`/`iss`/서명/만료를 검증하고 `sub` 기준으로 유저를 upsert한다.
- 세션은 **httpOnly 쿠키**(`kh_session`, SameSite=Lax, 기본 30일). 프론트가 토큰을 직접
  보관하지 않는다. 같은 오리진 배포라 `fetch`에 별도 설정이 필요 없지만,
  **로컬에서 오리진이 갈리면 `credentials: "include"`가 필요**하다.
- `onboarded: false`는 `level_band`가 아직 없다는 뜻이다 — 온보딩(레벨 자기선택) 화면으로
  보내고 `PATCH /api/me`로 저장하면 된다.

### ⚠️ 지금은 개발 모드다

`GOOGLE_CLIENT_ID`가 아직 없다. 그동안의 동작:

| 상황 | 동작 |
|---|---|
| **개발 모드** (client_id 없음, 현재) | 쿠키 없이도 dev 스텁 유저로 200. `POST /api/auth/google`은 **501** |
| **운영 모드** (client_id 설정됨) | 쿠키 없으면 **모든 엔드포인트 401** |

**프론트가 지금 해야 할 것**: 아직 로그인 UI를 만들 필요는 없지만, **401 응답 처리 경로는
지금 넣어두길 권한다.** client_id가 들어오는 순간 개발 환경 전체가 401로 바뀐다.
그 전까지는 현재처럼 동작한다.

client_id 발급 후 실제 로그인 흐름 연동은 이 스레드에서 이어서 진행하자.

## 3. 함께 바뀐 것

- `vocab.ja`(JSON) 저장이 유니코드 그대로가 됐다. 기존엔 `\uXXXX`로 저장돼 **일본어 검색이
  아예 안 걸렸다.** 응답 형태는 그대로다.
- `Attempt.used_choices`(C0002)와 `vocab_favorites` 테이블 마이그레이션 2건 추가.

## 아직 없는 것

| ID | 내용 | 막힌 이유 |
|---|---|---|
| B8 | EP 단계별(`video/point/practice`) 완료 | **프론트가 단계 정의를 확정해야 한다**(T0001에서 미회신) |
| — | `Episode.youtube_id` | 영상은 업로드됐으나 링크가 repo에 없다. 수집해서 채울 예정 |

## 수용 기준

- 프론트가 단어장 화면을 커서 페이지네이션·검색·즐겨찾기로 연결할 수 있다.
- 401 처리 경로가 준비되어 client_id 투입 시 화면이 깨지지 않는다.

## 검증

- 백엔드 테스트 **40개** 통과(신규 `test_vocab.py` 7, `test_auth.py` 8), 전체 **156개** 통과.
- 인증 테스트에 위조 쿠키·만료 쿠키 거부, 운영 모드에서 5개 엔드포인트 401 확인 포함.
- 실 데이터(어휘 10,198건) seed 후 검색·커서·즐겨찾기 실측. 본문 JSON은 실제 응답이다.

## 남은 질문

1. 단어장 화면에 `status` 3단계를 그대로 쓰는가, 아니면 다른 구분이 필요한가
2. B8 단계 정의 (T0001에서 이어짐)

## 응답 방법

`C0004_FE_to_BE_reply_C0003.md`를 만들고 `reply_to: C0003`으로 연결한다.
그다음 `docs/coordination/README.md`의 열린 스레드에서 최신 메시지, 다음 담당, 상태를 갱신한다.
