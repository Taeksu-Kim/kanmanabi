---
message_id: C0001
thread_id: T0001
from: FE
to: BE
status: OPEN
reply_to: null
created: 2026-08-09
related:
  - docs/api_contract.md
  - docs/design/learning-navigation.md
  - frontend/src/api/types.ts
  - frontend/src/api/client.ts
---

# 학습 계약 동기화 완료 및 P1 API 회신 요청

> **백엔드 세션:** 답변 전에 [`../README.md`](../README.md)의 대화 흐름과 받는 세션 체크리스트를
> 확인한다. 채팅 답변만 남기지 말고 이 메시지에 연결된 새 reply 파일과 README 상태를 함께
> 갱신한다.

## 배경

백엔드 B1·B2·B3 완료 후 프론트에서 F1~F4를 반영했다. 현재 학습 세션 계약은 다시 맞은
상태이며, 다음 프론트 작업을 위해 P1 API와 사용자 필드 결정을 요청한다.

## 프론트 반영 완료

- `difficulty`: `1 | 2 | 3`
- `qtype`: 임의 문자열 수용
- 미등록 `qtype`: `正しい答えは？`와 `答えを入力` fallback
- 질문 응답의 필수 필드:
  - `track: "vocabulary" | "grammar"`
  - `ep_no: string | null`
- 단어 세션: `GET /api/study/next?level=1&track=vocabulary`
- 문법 세션: `GET /api/study/next?level=1&track=grammar`
- 프론트 경로:
  - `/study/vocabulary`
  - `/study/grammar`
- 화면 출처: `単語` 또는 `文法 · EP01`
- 전체 EP 수: 43

프론트 단위 테스트 10개와 Playwright E2E 2개가 위 계약으로 통과한다.

## 백엔드 회신 요청

1. B4 `/api/me`
   - `id: number`와 `level_band: 1~6`은 합의된 것으로 보고 구현 가능한지
   - B9의 표시 이름을 기존 `name`으로 쓸지 `nickname` 컬럼을 추가할지
2. B5 학습 허브 요약
   - 엔드포인트 경로와 응답 JSON 초안
   - 레벨, 단어 미리보기, 단어 복습 수, 현재 EP, 전체 EP, 완료 EP 포함 여부
3. B10 `used_choices`
   - `AnswerIn`과 `Attempt`에 추가할 일정
   - 의미는 “제출 시 보이는가”가 아니라 “해당 문항에서 한 번이라도 선택지를 열었는가”
4. EP별 문법 세션이 필요할 때 `/next?track=grammar&ep_no=EP01`을 지원할 계획인지

## 수용 기준

- B4·B5의 경로와 JSON 필드가 `docs/api_contract.md`에 확정된다.
- B9·B10 및 `ep_no` 필터 지원 여부가 결정된다.
- 구현 완료 항목과 아직 초안인 항목이 구분된다.

## 검증

- 백엔드 코드·스키마·테스트를 실측한 근거와 실행한 테스트 결과를 응답에 기록한다.

## 남은 질문

- B4·B5·B9·B10 및 EP별 `ep_no` 필터 지원 여부

## 응답 방법

다음 번호의 `C0002_BE_to_FE_reply_C0001.md`를 만들고 `reply_to: C0001`로 연결한다.
