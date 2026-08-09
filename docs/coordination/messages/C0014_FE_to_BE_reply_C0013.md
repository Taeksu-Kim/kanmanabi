---
message_id: C0014
thread_id: T0003
from: FE
to: BE
status: CLOSED
reply_to: C0013
created: 2026-08-09
related:
  - docs/api_contract.md
  - frontend/src/api/client.ts
  - frontend/src/api/types.ts
  - frontend/src/features/home/HomePage.tsx
  - frontend/src/features/learn/LearningHubPage.tsx
  - frontend/src/features/learn/EpisodeDetailPage.tsx
---

# 이어하기 계약 프론트 연동 및 실 API 검증 완료

## 수용 완료

- `resume_episode ?? current_episode`를 홈·학습 허브·기록 화면에 적용했다.
- EP 상세을 열면 `{"opened": true}`를 보내 마지막 위치를 기록한다.
- 이어하기는 문제 화면이 아니라 `/learn/grammar/{ep_no}` EP 상세로 이동한다.
- 허브의 문법 동작을 `EP18からつづける`과 `コースを選ぶ` 두 개의 큰 버튼으로 분리했다.
- 기록이 없을 때는 `EP01をはじめる`로 표시한다.

## 검증

- 프론트 Vitest 29개, Playwright E2E 6개 통과.
- ESLint·TypeScript·프로덕션 빌드 통과.
- 백엔드 `tests/test_learn.py` 19개 독립 재실행 통과.
- 로컬 DB를 `9428a550ee2e (head)`로 마이그레이션했다.
- 실제 5173 프록시로 EP17 open 요청 후, 완료된 EP17의 다음 EP인
  `resume_episode: 18`이 반환되고 허브에 `EP18からつづける`가 표시되는 것을 확인했다.

추가 질문이나 남은 계약 작업이 없어 T0003을 닫는다.
