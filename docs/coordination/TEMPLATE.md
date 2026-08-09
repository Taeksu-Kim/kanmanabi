---
message_id: C0000
thread_id: T0000
from: FE
to: BE
status: OPEN
reply_to: null
created: YYYY-MM-DD
related:
  - docs/api_contract.md
---

# 제목

## 배경

왜 이 메시지가 필요한지 짧게 적는다.

## 전달 사항

- 이미 확정되거나 반영된 내용

## 요청 사항

1. 상대 세션이 답하거나 수행해야 하는 내용

## 수용 기준

- 완료 여부를 양쪽이 동일하게 판단할 수 있는 조건

## 검증

- 실행한 테스트 또는 코드·데이터 실측 결과

## 남은 질문

- 없으면 `없음`

## 응답 방법

`CNNNN_TO_to_FROM_reply_C0000.md`를 만들고 `reply_to: C0000`으로 연결한다.
그다음 `docs/coordination/README.md`의 열린 스레드에서 최신 메시지, 다음 담당, 상태를 갱신한다.
