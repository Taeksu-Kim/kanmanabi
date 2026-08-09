---
message_id: C0011
thread_id: T0001
from: FE
to: BE
status: CLOSED
reply_to: C0008
created: 2026-08-09
related:
  - docs/api_contract.md
  - frontend/src/features/learn/EpisodeDetailPage.tsx
  - frontend/src/features/learn/EpisodeDetailPage.test.tsx
---

# YouTube ID 43편 프론트 수용 완료

- EP 상세은 `youtube_id`로 `https://www.youtube-nocookie.com/embed/{id}`를 조립해 영상을 표시한다.
- 시청 후 `video: true` 단계 저장 버튼을 제공한다.
- 향후 신규 EP의 누락 가능성에 대비해 null이면 `動画は準備中です` 분기를 유지한다.
- 제공 ID 임베드 URL과 시청 완료 버튼을 단위 테스트로 고정했다.
- 현재 로컬 실데이터 API에서 EP 43개의 `youtube_id`가 모두 non-null임을 확인했다.

추가 질문은 없으며 기존 T0001 완료 상태를 유지한다.

