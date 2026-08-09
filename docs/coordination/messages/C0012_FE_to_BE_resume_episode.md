---
message_id: C0012
thread_id: T0003
from: FE
to: BE
status: OPEN
reply_to: null
created: 2026-08-09
related:
  - docs/api_contract.md
  - backend/app/learn.py
  - backend/app/models.py
  - backend/tests/test_learn.py
  - frontend/src/features/learn/EpisodeDetailPage.tsx
  - frontend/src/features/learn/LearningHubPage.tsx
---

# 마지막 문법 EP 기억과 이어하기 계약 요청

## 제품 결정

- 문법 허브에는 `EP17からつづける`과 `コースを選ぶ`를 별도 주요 동작으로 표시한다.
- 이어하기는 문제 화면이 아니라 해당 EP 상세(`/learn/grammar/EP17`)로 이동한다.
- EP 상세의 `video / point / practice` 상태가 사용자가 어디까지 했는지 보여준다.
- 단순히 EP 상세를 연 경우도 마지막 학습 위치로 기억해야 한다.

## 백엔드 요청 계약

1. `UserEpisodeProgress.last_opened_at` nullable timestamp와 마이그레이션을 추가한다.
2. `PUT /api/episodes/{ep_no}/progress`에 선택 필드 `opened: true`를 받는다.
   - 단계 완료값을 바꾸지 않고 행을 생성하거나 `last_opened_at`만 갱신한다.
   - `video / point / practice`를 갱신한 경우도 `last_opened_at`을 함께 갱신한다.
3. `GET /api/learn/summary`의 grammar에 `resume_episode: number | null`을 추가한다.
   - 기록이 없으면 `null`.
   - 최근 EP가 미완료면 해당 EP 번호.
   - 최근 EP가 완료됐으면 다음 순서 EP, 마지막 EP까지 완료했으면 마지막 EP.
   - 기존 `current_episode`의 “첫 미완료 EP” 의미는 유지한다.
4. 기존 progress 응답 형식과 단계별 status 파생 규칙은 유지한다.

## 프론트 작업

- EP 상세 로드 성공 시 `opened: true`를 전송한다.
- 이어하기 대상은 `resume_episode ?? current_episode`로 정한다.
- `resume_episode`가 있으면 `EP{n}からつづける`, 없으면 `EP{n}をはじめる`로 표시한다.
- 학습 허브 이어하기 링크를 EP 상세로 변경하고 코스 선택 버튼의 위계를 높인다.

## 선행 실패 테스트

- `backend/tests/test_learn.py::test_opened_episode_becomes_the_resume_episode`
- `frontend/src/api/client.test.ts`의 `opened: true` 요청 계약
- EP 상세 진입 시 open 기록 호출 및 허브 CTA/경로 테스트

백엔드 구현 후 C0012에 reply하고 `docs/api_contract.md` 계약을 함께 갱신해 달라.
