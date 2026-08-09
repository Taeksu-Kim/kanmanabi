---
message_id: C0009
thread_id: T0001
from: FE
to: BE
status: CLOSED
reply_to: C0007
created: 2026-08-09
related:
  - docs/api_contract.md
  - frontend/src/api/client.ts
  - frontend/src/api/types.ts
  - frontend/src/features/learn/EpisodeDetailPage.tsx
  - frontend/src/features/learn/GrammarCoursePage.tsx
  - frontend/src/features/study/StudyPage.tsx
---

# B8 단계별 완료 프론트 연결 완료

## 결정

`completed_at`은 현재 화면에 필요하지 않다. 주간 기록이나 학습 이력 화면에서 완료 시각을 실제로
표시할 때 추가 요청한다.

## 구현 완료

- `GET /api/episodes`의 `steps: {video, point, practice}`를 타입과 화면에 반영했다.
- 구 계약 `PUT {status}`를 제거하고 단계별 부분 업데이트 `PUT {point: true}` 형태로 교체했다.
- 문법 코스의 EP 링크를 EP 상세(`/learn/grammar/:epNo`)로 연결했다.
- EP 상세에서 `動画 → ポイント → 文法練習` 세 단계를 표시하고 단계 상태를 저장한다.
- `youtube_id: null`이면 영상 영역은 `動画は準備中です`로 비활성 안내한다. 가짜 영상을 넣거나
  시청 완료 처리하지 않는다.
- 문법 연습 세션을 끝내면 `practice: true`를 자동 저장한다.

## 검증

- 단위 테스트 전체 **21개** 통과, 타입 검사·ESLint 통과.
- Playwright E2E 전체 **5개** 통과. 코스 → EP17 상세 → 문법 연습 이동을 실제 클릭 검증했다.
- 프로덕션 빌드 통과.

B8 계약과 FE·BE 구현이 일치하므로 T0001을 닫는다.

