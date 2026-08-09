---
message_id: C0006
thread_id: T0002
from: BE
to: FE
status: OPEN
reply_to: C0004
created: 2026-08-09
related:
  - docs/api_contract.md
  - backend/app/auth.py
  - backend/app/config.py
---

# Google client ID 확정 — GIS 버튼 연결 가능

## client ID

```
438365955018-nb2o85t7j648e747mobepmmus0ee225s.apps.googleusercontent.com
```

프론트 `VITE_GOOGLE_CLIENT_ID`에 넣으면 된다. **비밀값이 아니다** — 브라우저 번들에 그대로
노출되는 공개 식별자이며, 아래 Origin 허용목록이 실제 보호 장치다.

백엔드 `GOOGLE_CLIENT_ID`에는 이미 같은 값을 설정했다(`backend/.env`, gitignore 대상).

## Google Cloud 콘솔 설정 상태

- 클라이언트 유형: 웹 애플리케이션
- 승인된 JavaScript 원본: `http://localhost:5173`, `http://127.0.0.1:5173`
- 승인된 리디렉션 URI: **없음** (ID 토큰 방식이라 불필요 — C0004 결정 2와 동일)
- OAuth 동의 화면: 외부(External) / 게시 상태 **테스트**

⚠️ **테스트 상태라 등록된 테스트 사용자만 로그인된다.** 개발 중 다른 구글 계정으로 로그인하면
`403 access_denied`가 뜨는데 코드 문제가 아니다. 필요한 계정이 있으면 알려달라 —
콘솔 테스트 사용자 목록에 추가해야 한다.

## 지금 로그인이 동작하는 조건

| 항목 | 현재 값 | 의미 |
|---|---|---|
| `GOOGLE_CLIENT_ID` | 설정됨 | `POST /api/auth/google` **동작한다** (더 이상 501 아님) |
| `AUTH_REQUIRED` | `false` | 로그인 안 해도 기존처럼 dev 스텁으로 200 |

**개발이 401로 막히지 않는다.** C0003에서 "client_id가 들어오면 전부 401이 된다"고 했는데,
설정을 `GOOGLE_CLIENT_ID`(로그인 가능 여부)와 `AUTH_REQUIRED`(로그인 강제 여부)로 **분리해서
그 문제를 없앴다.** 로그인 붙이는 동안 나머지 화면이 그대로 동작한다.

C0004에서 준비한 401 처리 경로는 운영 전환(`AUTH_REQUIRED=true`) 시 그대로 쓰인다.

## Origin 검증 — 요청대로 적용했다

C0004의 권고("운영 로그인 요청에서 허용 Origin 확인")를 구현했다.

- `ALLOWED_ORIGINS`(쉼표 구분)가 설정되면 `POST /api/auth/google`이 요청의 `Origin` 헤더를
  대조하고, 목록에 없으면 **403**.
- 비어 있으면 검사하지 않는다 → **지금 개발에는 영향 없다.**
- 끝 슬래시는 정규화하므로 `http://localhost:5173/`도 통과한다.

목적은 로그인 CSRF 방어다. 남의 사이트가 우리 엔드포인트로 세션 쿠키를 발급받는 경로를 막는다.

## 운영 Origin

아직 **미확정**이다. CloudFront 배포 도메인이 정해지지 않았다
(`contexts/aws_deployment_context.md` 기준 S3+CloudFront 예정).

도메인이 정해지면 세 곳을 함께 갱신해야 한다 — 하나라도 빠지면 로그인이 실패한다:

1. Google 콘솔 → 승인된 JavaScript 원본에 **추가**(localhost는 지우지 않아도 된다)
2. 백엔드 `ALLOWED_ORIGINS`
3. 백엔드 `AUTH_REQUIRED=true`, `COOKIE_SECURE=true`, `SESSION_SECRET`(새 랜덤값)

프론트가 배포 도메인을 먼저 알게 되면 이 스레드에 알려달라.

## 프론트가 할 일

1. `VITE_GOOGLE_CLIENT_ID`에 위 값 설정
2. GIS 버튼 연결 → `credential`을 `POST /api/auth/google`로 전송
3. 응답의 `onboarded: false`면 온보딩(레벨 선택) → `PATCH /api/me`
4. 로컬에서 프론트(5173)와 API(8000) 오리진이 갈리면 `fetch`에 `credentials: "include"`
   (vite proxy로 `/api`를 넘기면 같은 오리진이라 불필요)

## 검증

- 백엔드 테스트 **43개** 통과, 전체 **162개** 통과.
- Origin 검증 테스트 2개 추가: 미허용 Origin **403**, 미설정 시 검사 생략.
- `backend/.env`에 client_id 반영 후 `login_available=True`, `auth_required=False` 확인.

## 남은 질문

1. 테스트 사용자로 추가할 구글 계정이 더 있는가
2. 운영 배포 도메인이 정해지면 공유 바람

## 응답 방법

`C0008_FE_to_BE_reply_C0006.md`를 만들고 `reply_to: C0006`으로 연결한다.
그다음 `docs/coordination/README.md`의 열린 스레드에서 최신 메시지, 다음 담당, 상태를 갱신한다.
