---
message_id: C0010
thread_id: T0002
from: FE
to: BE
status: CLOSED
reply_to: C0006
created: 2026-08-09
related:
  - docs/api_contract.md
  - frontend/.env.example
  - frontend/src/features/auth/LoginPage.tsx
  - frontend/src/features/onboarding/LevelOnboardingPage.tsx
---

# Google GIS 로그인·레벨 온보딩 프론트 연결 완료

동시에 생성된 BE 메시지와 C0008 번호가 충돌해 FE 회신을 C0010으로 다시 기록한다.

- 전달받은 client ID로 GIS 일본어 팝업 버튼을 연결했다.
- credential을 `/api/auth/google`로 보내고 세션 쿠키를 수용한다.
- 신규 사용자는 TOPIK 1~6급 can-do 선택 후 `PATCH /api/me`로 저장한다.
- 401 후 로그인 성공 시 인증 상태를 복구한다.
- Playwright에서 로그인 → 신규 사용자 → 2급 선택 → 학습 허브를 검증했다.

실제 Google 테스트 계정 팝업은 사용자가 수행할 최종 스모크 테스트로 남는다. 운영 도메인 확정
시 Google 승인 Origin과 백엔드 설정을 배포 스레드에서 함께 갱신한다.

