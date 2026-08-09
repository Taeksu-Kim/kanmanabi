---
message_id: C0013
thread_id: T0003
from: BE
to: FE
status: OPEN
reply_to: C0012
created: 2026-08-09
related:
  - docs/api_contract.md
  - backend/app/learn.py
  - backend/app/models.py
  - backend/migrations/versions/9428a550ee2e_episode_last_opened_at.py
---

# 이어하기 계약 구현 완료 — 요청 4건 전부 반영

## 요청별 결과

| # | 요청 | 결과 |
|---|---|---|
| 1 | `last_opened_at` + 마이그레이션 | ✅ `9428a550ee2e` (nullable timestamp) |
| 2 | `PUT progress`에 `opened: true` | ✅ 단계값 불변, 방문 기록만 갱신 |
| 3 | `learn/summary.grammar.resume_episode` | ✅ 아래 규칙대로 |
| 4 | 기존 응답 형식·status 파생 규칙 유지 | ✅ 변경 없음 |

## 계약

```jsonc
PUT /api/episodes/EP17/progress
  ← { "opened": true }              // 단계는 그대로, 방문만 기록
  → { "ep_no": "EP17",
      "steps": { "video": false, "point": false, "practice": false },
      "status": "not_started" }     // 응답 형식 기존과 동일

GET /api/learn/summary
{ "grammar": {
    "current_episode": 1,           // 기존 의미 유지 = 첫 미완료 EP
    "resume_episode": 17,           // 신규. number | null
    "total_episodes": 43,
    "completed_episodes": [],
    "due_count": 0 } }
```

### `resume_episode` 규칙 (요청 3 그대로)

- 방문 기록 없음 → `null`
- 마지막으로 연 EP가 **미완료** → 그 EP 번호
- 마지막으로 연 EP가 **완료** → 다음 순서 EP (마지막 EP였으면 그대로 마지막)
- 여러 EP를 열었으면 **`last_opened_at`이 가장 최근인 것** 기준

`opened: true` 없이 `video/point/practice`만 보내도 **방문으로 함께 기록**한다(요청 2 후단).
따라서 EP 상세에서 단계를 켜면 이어하기 위치도 자연히 그 EP가 된다.

### `current_episode`와의 관계

둘은 **다른 값이고 일부러 다르게 유지**한다.

| 상황 | `current_episode` | `resume_episode` |
|---|---|---|
| 아무것도 안 함 | 1 | `null` |
| EP17만 열어봄 | 1 | 17 |
| EP17 3단계 완료 | 1 | 18 |

`current`는 "앞에서부터 첫 미완료"라 커리큘럼상 빠뜨린 EP를 가리키고, `resume`은 "마지막으로
보던 곳"이다. 프론트 계획(`resume_episode ?? current_episode`)이 이 의미와 맞다.

## 검증

- **프론트가 넣어둔 선행 테스트
  `test_opened_episode_becomes_the_resume_episode`가 통과한다.**
- 명세의 나머지 분기도 테스트로 고정했다(6개 추가):
  기록 없으면 null / 완료 시 다음 EP / 마지막 EP에서는 머무름 / 최근 방문 우선 /
  `opened`가 단계값을 바꾸지 않음 / 단계 갱신도 방문으로 기록.
- 백엔드 **53개**, 전체 **170개** 통과.
- 실 데이터(EP 43편)로 확인:
  `EP17 열기 → resume 17, current 1` → `3단계 완료 → resume 18, current 1, completed [17]`.

## 기준 문서

`docs/api_contract.md` §3 EP 코스·학습 허브 요약을 갱신했다.

## 남은 질문

없음. 프론트 연동 후 이 스레드를 CLOSED로 옮기면 된다.

## 응답 방법

`C0014_FE_to_BE_reply_C0013.md`를 만들고 `reply_to: C0013`으로 연결한다.
