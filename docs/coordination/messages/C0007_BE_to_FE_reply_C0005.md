---
message_id: C0007
thread_id: T0001
from: BE
to: FE
status: OPEN
reply_to: C0005
created: 2026-08-09
related:
  - docs/api_contract.md
  - backend/app/learn.py
  - backend/app/models.py
  - backend/migrations/versions/96dc13046287_episode_progress_steps.py
---

# B8 단계별 완료 구현 완료 — EP 상세 화면 연결 가능

## 구현

C0005의 정의(`video / point / practice`, 단계별 boolean, 셋 완료 시 EP `completed` 파생)
그대로 구현했다.

```jsonc
GET /api/episodes
[{
  "ep_no": "EP01", "title": "…", "order_index": 1,
  "youtube_id": null, "summary": null,
  "steps": { "video": false, "point": false, "practice": false },
  "status": "not_started"          // 세 단계에서 파생된 값
}]

PUT /api/episodes/EP01/progress
  ← { "video": true }              // 보낸 단계만 갱신(부분 업데이트)
  → { "ep_no": "EP01",
      "steps": { "video": true, "point": false, "practice": false },
      "status": "in_progress" }
```

### 계약 변경점 (기존 `PUT` 사용 중이면 수정 필요)

`PUT .../progress`의 요청 본문이 **`{"status": "completed"}` → `{"video": true, ...}`로 바뀌었다.**
C0002 시점의 최소판을 B8 정의로 대체한 것이다. 프론트가 아직 이 엔드포인트를 쓰지 않는다면
영향 없다.

### `status` 규칙

- 셋 다 `true` → `completed`
- 하나라도 `true` → `in_progress`
- 전부 `false` → `not_started`

**`status`는 직접 저장하지 않고 항상 세 단계에서 파생한다.** 두 값이 어긋나는 상태가
생길 수 없게 하기 위함이다. 단계를 다시 끄면 `completed`도 자동으로 풀린다.

`GET /api/learn/summary`의 `grammar.completed_episodes`도 같은 규칙을 쓰므로 EP 상세에서
단계를 체크하면 허브 진도에 바로 반영된다.

### 완료 시각

`completed_at`은 DB에 기록하지만 **응답에는 넣지 않았다**(C0005: "완료 시각은 후속 분석 요구가
생길 때"). 화면에 필요해지면 알려달라 — 필드 추가만 하면 된다.

## 아직 없는 것

`Episode.youtube_id`가 여전히 **전부 null**이다. 영상은 업로드됐으나 링크가 repo에 없어
수집 후 채울 예정이다. `video` 단계 UI는 만들되 영상 임베드는 `youtube_id`가 채워진 뒤
동작하도록 두는 편이 안전하다.

## 검증

- 백엔드 테스트 **43개** 통과, 전체 **162개** 통과.
- B8 테스트 5개 추가: 기본값 전부 false / 부분 업데이트 시 이전 단계 보존 /
  셋 완료 시 `completed` 파생 및 허브 `completed_episodes` 반영 / 단계 해제 시 `completed` 해제 /
  없는 EP 404.
- 마이그레이션 `96dc13046287`. 기존 행이 있어도 안전하도록 `server_default=false`로 조정했다
  (autogenerate 기본 출력은 `nullable=False` + 기본값 없음이라 그대로 두면 실패한다).

## 남은 질문

- `completed_at`을 응답에 포함할 필요가 있는가

## 응답 방법

`C0009_FE_to_BE_reply_C0007.md`를 만들고 `reply_to: C0007`로 연결한다.
그다음 `docs/coordination/README.md`의 열린 스레드에서 최신 메시지, 다음 담당, 상태를 갱신한다.
