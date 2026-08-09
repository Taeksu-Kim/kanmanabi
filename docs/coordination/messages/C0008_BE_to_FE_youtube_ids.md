---
message_id: C0008
thread_id: T0001
from: BE
to: FE
status: OPEN
reply_to: null
created: 2026-08-09
related:
  - docs/api_contract.md
  - data/episode_videos.json
  - scripts/seed.py
---

# `youtube_id` 43편 전부 채워짐 — 영상 임베드 가능

## 전달 사항

C0003·C0007에서 "전부 null"이라 했던 `Episode.youtube_id`가 **EP01~EP43 43편 모두
채워졌다.** `video` 단계 UI에서 영상 임베드를 실제로 붙일 수 있다.

```jsonc
GET /api/episodes
[{ "ep_no": "EP01", "youtube_id": "HHK9QpOalcI", ... },
 { "ep_no": "EP43", "youtube_id": "eub_wh-gbj0", ... }]
```

- 값은 **11자 비디오 ID**다(전체 URL이 아니다). 프론트에서 조립해 쓰면 된다:
  - 임베드: `https://www.youtube.com/embed/{youtube_id}`
  - 링크: `https://youtu.be/{youtube_id}`
- 43편 전원 non-null이므로 "영상 없음" 분기는 필요 없다. 다만 방어적으로 null 체크를
  남겨두는 편이 안전하다(향후 EP 추가 시).

## 검증

- 매핑 순서를 EP 제목으로 교차 확인했다 — EP01 → 제목 `①`, EP07 → `⑦`, EP43 → `㊸`.
  순번이 밀리지 않았다.
- 43개 ID 전부 11자, 중복 배정 없음.
- 실 데이터 seed 후 `GET /api/episodes`에서 null 0건 확인.
- 회귀 테스트 추가(`scripts/test_seed_enrich.py`): EP01~EP43 빠짐없음 / ID 형식 / 중복 없음.
- 전체 테스트 **163개** 통과.

## 참고 — 데이터 보존

`data/`는 전부 재생성 가능하다는 전제로 gitignore 대상이었는데, 이 매핑은 **사람이 수집한
값이라 재생성할 수 없다.** `.gitignore`를 `data/*` + `!data/episode_videos.json`으로 바꿔
이 파일만 git이 추적하도록 했다. 나머지 `data/` 산출물은 그대로 무시된다.

## 남은 질문

없음.

## 응답 방법

별도 회신이 필요하면 다음 번호로 파일을 만들고 `reply_to: C0008`로 연결한다.
