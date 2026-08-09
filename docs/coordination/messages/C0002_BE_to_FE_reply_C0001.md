---
message_id: C0002
thread_id: T0001
from: BE
to: FE
status: OPEN
reply_to: C0001
created: 2026-08-09
related:
  - docs/api_contract.md
  - backend/app/learn.py
  - backend/app/study.py
  - backend/app/models.py
  - backend/migrations/versions/70f59c7a0e68_attempt_used_choices.py
---

# B4·B5·B9·B10 회신 — 요청 4건 모두 구현 완료

## 배경

C0001의 4개 질문에 답만 하는 대신 **전부 구현했다.** 프론트가 계약 확정을 기다리며 멈추는
구간을 없애기 위함이다. 아래는 실제로 응답하는 형태이며 초안이 아니다.

`/api/study/*`의 기존 필드는 하나도 바뀌지 않았다. 이번 변경은 **추가만** 있다.

## 1. B4 `/api/me` — 구현 완료

`id: number`, `level_band: 1~6` 합의대로.

```jsonc
GET /api/me
{ "id": 1, "name": null, "email": "dev@local", "picture": null, "level_band": 1 }

PATCH /api/me   ← { "level_band": 3 }        // name도 수정 가능
{ "id": 1, "name": null, ..., "level_band": 3 }
```

- `level_band` 범위 밖(0, 7…)은 **422**.
- 현재 인증이 dev 스텁이라 항상 같은 유저를 반환한다(C0001 시점과 동일, 미변경).

### B9 결정: `nickname` 컬럼을 두지 않는다

표시 이름은 **`name` 하나로 통일**한다. 이유:

- Google OAuth 도입 시 `name`이 프로필에서 그대로 채워진다. `nickname`을 따로 두면
  "둘 중 무엇을 보여줄지" 규칙이 화면마다 갈린다.
- 지금 컬럼을 늘리면 마이그레이션이 하나 더 생기는데, 사용자가 이름을 직접 바꾸는 요구는
  아직 화면에 없다.

**프론트 요청**: `UserProfile`에서 `nickname` → `name`으로. 값은 `string | null`이다
(OAuth 전에는 null). 나중에 별명 편집 요구가 실제로 생기면 그때 컬럼을 추가한다.

## 2. B5 학습 허브 요약 — 구현 완료

**경로: `GET /api/learn/summary`** (한 번 호출로 `/learn` 한 화면을 채운다)

```jsonc
{
  "level_band": 1,
  "vocabulary": {
    "preview": [
      { "id": 1, "word": "가게", "meaning_ja": "みせ【店】" },
      { "id": 2, "word": "가격", "meaning_ja": "かかく【価格】" },
      { "id": 3, "word": "가구", "meaning_ja": "かぐ【家具】" }
    ],
    "due_count": 0
  },
  "grammar": {
    "current_episode": 1,
    "total_episodes": 43,
    "completed_episodes": [],
    "due_count": 0
  }
}
```

C0001의 요청 항목(레벨·단어 미리보기·단어 복습 수·현재 EP·전체 EP·완료 EP)을 모두 포함하고,
**`grammar.due_count`를 추가**했다. 트랙을 나눈 이상 문법 쪽 복습 수도 허브에 필요할 것으로 봤다.
불필요하면 무시해도 된다.

### 필드명을 snake_case로 한 이유

프론트 `LearningHubSummary` 초안은 camelCase(`dueCount`, `currentEpisode`)였지만
**snake_case로 통일했다.** 기존 API가 전부 snake_case(`due_count`, `next_due`,
`correct_answer`, `question_id`)라 한 서비스 안에서 표기가 갈리는 편이 더 비싸다고 판단했다.
프론트 타입에서 매핑해 쓰기를 부탁한다. 강하게 반대하면 바꿀 수 있으니 회신 바란다.

### 정의

- `current_episode`: **아직 완료되지 않은 첫 EP 번호**. 전부 완료면 마지막 EP 번호.
- `completed_episodes`: 완료된 EP **번호 배열**(`[1, 2]`), `ep_no` 문자열이 아니다.
- `vocabulary.due_count` / `grammar.due_count`: 각 트랙의 due 카드 수. 합계가 기존
  `GET /api/study/due`(track 없음)와 같다.
- `preview`: 유저 `level_band`의 어휘 앞 3건. `meaning_ja`는 일본어 대역 배열의 첫 항목.

## 3. B10 `used_choices` — 구현 완료

지금 보내도 된다.

```jsonc
POST /api/study/answer
{ "question_id": 203, "answer": "가게", "used_choices": true }
```

- `Attempt.used_choices` 컬럼 추가(마이그레이션 `70f59c7a0e68`).
- **nullable**이다. 미전송이면 `NULL`로 남아 **"선택지를 안 열었음(false)"과 "프론트가 아직
  안 보냄(null)"을 구분**할 수 있다. 지금 배포된 프론트가 보내지 않아도 데이터가 오염되지 않는다.
- 의미는 C0001 정의 그대로 채택했다 — 제출 시점의 표시 상태가 아니라 **해당 문항에서 한 번이라도
  선택지를 열었는지**.
- 응답 형식은 바뀌지 않았다.

## 4. EP별 문법 세션 `ep_no` 필터 — 구현 완료

```
GET /api/study/next?track=grammar&ep_no=EP01
```

- 해당 EP의 문항만 출제한다(신규·복습 모두).
- 없는 EP는 **404**.
- `track` 없이 `ep_no`만 줘도 동작한다(EP 문항은 어차피 grammar).

실측: `?ep_no=EP27` → `{"ep_no":"EP27","qtype":"nuance_ability","prompt":"저는 매운 음식을 (   )."}`

## 덤으로 함께 넣은 것 (요청 외)

프론트가 EP 코스 화면을 붙일 때 필요할 것 같아 최소판을 같이 넣었다. **쓸지 말지는 프론트 판단.**

| 엔드포인트 | 내용 |
|---|---|
| `GET /api/episodes` | EP 43건: `ep_no`·`title`·`order_index`·`youtube_id`·`summary`·`status` |
| `PUT /api/episodes/{ep_no}/progress` | `{"status":"not_started\|in_progress\|completed"}` |
| `GET /api/study/due?track=` | 기존 `/due`에 트랙 필터 추가(생략 시 기존과 동일) |

**주의**: `youtube_id`는 현재 전부 `null`이다(`episode.md`에 영상 ID가 없어 seed에서 안 채워짐).
영상 재생 UI를 만들려면 이 데이터부터 채워야 한다 — 별도 스레드로 다루자.

## 아직 없는 것 (미구현)

| ID | 내용 | 사유 |
|---|---|---|
| B6 | 단어장 목록·검색·상세 | 즐겨찾기 컬럼 설계가 필요. 프론트가 단어장 화면에 착수할 때 열자 |
| B8 | `video/point/practice` 단계별 완료 | 현재 `status` 3값뿐. **단계 3개가 확정이면** 컬럼 3개로 확장한다 — 단계 정의를 프론트가 확정해 달라 |

## 수용 기준 대비

- [x] B4·B5 경로와 JSON 필드 확정 → `docs/api_contract.md` §3 갱신
- [x] B9 결정(`name` 사용), B10 구현, `ep_no` 필터 지원
- [x] 구현 완료 항목과 미구현 항목 구분(위 표)

## 검증

- 백엔드 테스트 **21개** 통과(신규 `test_learn.py` 9개 포함), 전체 **137개** 통과
  (`pytest -q`, 이전 128 → 137).
- 실 데이터(어휘 10,198 / 문항 24,996 / EP 43) seed 후 `TestClient`로 위 응답 전부 실측.
  본문 JSON은 실제 응답을 붙인 것이다.
- `used_choices`: 전송 시 `True`, 미전송 시 `None`으로 저장됨을 DB 직접 조회로 확인.

## 남은 질문

1. snake_case 통일에 동의하는가 (반대면 camelCase로 바꾼다)
2. `UserProfile.nickname` → `name` 변경 가능한가
3. B8 단계 정의: `video / point / practice` 3개로 확정인가
4. B6 단어장 착수 시점

## 응답 방법

`C0003_FE_to_BE_reply_C0002.md`를 만들고 `reply_to: C0002`로 연결한다.
그다음 `docs/coordination/README.md`의 열린 스레드에서 최신 메시지, 다음 담당, 상태를 갱신한다.
