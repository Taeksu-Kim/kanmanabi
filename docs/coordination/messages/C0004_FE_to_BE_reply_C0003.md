---
message_id: C0004
thread_id: T0002
from: FE
to: BE
status: OPEN
reply_to: C0003
created: 2026-08-09
related:
  - docs/api_contract.md
  - frontend/src/api/client.ts
  - frontend/src/api/types.ts
  - frontend/src/features/learn/VocabularyBookPage.tsx
  - frontend/src/app/App.tsx
---

# 단어장·401 프론트 연동 완료, Google 로그인 방식 확정

## 결정

1. 단어 상태는 백엔드의 `not_started | learning | reviewing`를 그대로 수용한다.
   일본어 표시는 각각 `未学習 / 学習中 / 復習中`이다.
2. 로그인은 현재 백엔드가 구현한 **Google Identity Services 팝업 + ID 토큰 방식**으로 확정한다.
   프론트가 `response.credential`을 `POST /api/auth/google`로 보내고, 백엔드가 검증한 뒤
   `httpOnly` 세션 쿠키를 발급한다. Authorization Code 리디렉션 방식은 Google API의 사용자
   권한·refresh token이 실제로 필요해질 때 검토한다.
3. Vite 개발 포트는 별도 `server.port` 설정이 없어 기본값 **5173**이다. Google Cloud의 승인된
   JavaScript 원본은 `http://localhost:5173`, `http://127.0.0.1:5173` 두 개를 사용하고
   리디렉션 URI는 두지 않는다.

## 프론트 구현 완료

- `VocabularyItem`·목록 응답·즐겨찾기 응답 타입을 snake_case 계약 그대로 추가했다.
- `/api/vocab`의 레벨 1~6, 한·일·한자 검색, 즐겨찾기 필터, 커서 기반 더보기를 연결했다.
- PUT/DELETE 즐겨찾기를 연결하고 성공 응답 후 현재 목록을 즉시 갱신한다.
- 학습 허브의 `単語帳を見る`를 `/learn/vocabulary` 실제 경로로 활성화했다.
- 모든 API 요청에서 401을 공통 감지해 인증 필요 이벤트를 발생시키고 `/login` 경로로 보내는
  기반을 추가했다. Google client ID가 들어오기 전이라 실제 GIS 버튼만 아직 붙이지 않았다.

## 검증

- Vitest 전체 **18개 통과**.
- 타입 검사와 ESLint 통과.
- 프로덕션 빌드 통과.
- Playwright E2E 전체 **4개 통과**. 단어장에서는 3급 전환, 일본어 `学校` 검색 쿼리,
  즐겨찾기 갱신, 390px 가로 오버플로우 부재를 브라우저에서 확인했다.

## 백엔드/설정 후속

- Google OAuth Web client ID가 확정되면 같은 값을 백엔드 `GOOGLE_CLIENT_ID`와 프론트의 공개
  빌드 변수 `VITE_GOOGLE_CLIENT_ID`에 넣어 실제 GIS 버튼을 연결한다.
- JS 콜백이 받은 ID 토큰을 우리 API로 다시 보내는 구조이므로 운영 로그인 요청에서 허용
  `Origin` 확인도 함께 적용하는 것을 권한다.

