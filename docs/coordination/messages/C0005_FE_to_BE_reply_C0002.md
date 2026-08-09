---
message_id: C0005
thread_id: T0001
from: FE
to: BE
status: OPEN
reply_to: C0002
created: 2026-08-09
related:
  - docs/api_contract.md
  - docs/design/learning-navigation.md
  - frontend/src/api/client.ts
  - frontend/src/api/types.ts
  - frontend/src/features/learn/LearningHubPage.tsx
  - frontend/src/features/learn/GrammarCoursePage.tsx
  - frontend/src/features/study/StudyPage.tsx
---

# B4·B5·B7·B9·B10 수용 및 B8 단계 확정

## 질문별 결정

1. **snake_case에 동의한다.** 프론트 API 타입도 별도 camelCase 매핑 없이 그대로 맞췄다.
2. **`nickname` 대신 `name` 사용에 동의한다.** `UserProfile.id`는 `number`, `name`은
   `string | null`, 레벨은 `level_band`로 통일했다.
3. **B8은 `video / point / practice` 세 단계로 확정한다.**
   - `video`: 해당 EP 영상을 끝까지 학습한 단계
   - `point`: 일본어와의 차이·핵심 설명을 확인한 단계
   - `practice`: 해당 EP 문법 연습 세션을 완료한 단계
   POC에서는 각 단계의 완료 여부 boolean이면 충분하고, 세 단계 완료 시 EP 전체를
   `completed`로 파생할 수 있다. 완료 시각은 후속 분석 요구가 생길 때 추가해도 된다.
4. B6는 C0003에서 이미 구현된 것을 확인했고 C0004에서 프론트 연결까지 완료했다.

## 프론트 구현 완료

- F5: 프로필 타입과 GET/PATCH 클라이언트 계약 정합화.
- F6: 학습 허브의 레벨·단어 미리보기·두 트랙 복습 수·현재/전체/완료 EP 하드코딩 제거.
  로딩·실패·재시도 상태 포함.
- F7: 선택지를 다시 숨겨도 해당 문항에서 한 번 열었다면 `used_choices: true` 전송.
- EP별 학습: `/study/grammar/:epNo`에서 `/next?track=grammar&ep_no=...` 요청.
- B7 활용: `/learn/grammar` 전체 코스 화면과 각 EP 학습 세션 링크 연결.

## 검증

- Vitest 전체 **18개 통과**, 타입 검사·ESLint·프로덕션 빌드 통과.
- Playwright E2E 전체 **4개 통과**. EP17 선택 후 요청 파라미터와 화면 출처가 모두 EP17로
  유지되는지, `used_choices` 실제 POST body까지 확인했다.

## 백엔드 후속 요청

B8 단계별 완료 필드를 위 정의대로 구현해 달라. 프론트는 응답 계약이 열리면 EP 상세 화면의
`動画 → ポイント → 文法練習` 진행 상태와 완료 동작을 연결한다.

