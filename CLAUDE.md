# korean_helper

## 프로젝트 개요

한국어를 공부하는 **일본인 학습자를 보조하는 웹서비스**. 이미 구축된 콘텐츠 자산(`kr_study_material`, 문법 강의 42편)을 웹 학습 경험으로 재활용한다.

**현재 단계**: 기획·설계 단계. 아직 코드 없음(문서만 존재).

## 문서 맵

작업 전 관련 문서를 먼저 확인한다. 결정이 바뀌면 아래 문서를 같은 턴에 갱신한다.

| 문서 | 내용 |
|------|------|
| `docs/status.md` | **진행 상태·재개 가이드** (커맨드·luna 승인·남은 EP) — 세션 재개 시 먼저 |
| `docs/project_overview.md` | 큰 맥락·현재 시스템·확정 결정 (최상위 컨텍스트) |
| `docs/product_plan.md` | 페인포인트·제품 테제·스코프·솔루션 방향 + **Parking Lot(추후 검토)** |
| `docs/todo.md` | 착수 전 **검증·결정이 필요한 실제 할 일** |
| `docs/data_model.md` | DB 데이터 모델 (엔티티·ER·인증) |
| `docs/question_generation.md` | 문제 생성 설계 (로직·오답·벡터·LLM 경계·순서) |
| `docs/ep_grammar_map.md` | EP별 문법포인트·생성타입(T1로직/T2luna보조/T3luna저작) |
| `docs/frontend_brief.md` | 프론트 세션 핸드오프 (API 계약·UX·디자인 방향) |
| `contexts/aws_deployment_context.md` | 인프라·배포 설계 (AWS) |
| `contexts/local_llm_context.md` | 로컬 vLLM 서버 실행·접속 메모 (개발용 LLM) |
| `contexts/vector_db_context.md` | 벡터검색 스택 — 임베더 vLLM 실행 + Qdrant 분리 collection |
| `contexts/codex_context.md` | Codex(gpt-5.6-luna) 추론 사용법 — 소프트 생성용(예문·해설) |

## 콘텐츠 원천 — `kr_study_material`

- 경로: `/mnt/d/workspace/kr_study_material` (별도 repo, 상세는 해당 repo의 `CLAUDE.md`)
- 일본어로 한국어 문법을 설명하는 블로그 → YouTube 강의 파이프라인. `docs/episodes/EP01~EP42`에 EP별 산출물(`episode.md`, 슬라이드, TTS 스크립트, SRT, 음성, mp4)이 쌓여 있다.
- **재활용 원칙**: 콘텐츠를 새로 만들지 않고 **있는 것을 태운다.** 특히 각 EP엔 이미 **연습문제+정답(난이도 ★☆☆~★★★)**, SRT, `script_for_tts.md`가 있어 문제·채점·받아쓰기의 재료로 바로 쓸 수 있다.
- 이 repo에서 `kr_study_material` 파일을 **수정하지 않는다** (읽기·참조 전용).

## 확정된 결정

- **타깃**: 입문~초급 일본인 학습자 (콘텐츠가 초급 위주, ≈TOPIK 1~2급).
- **설명 원칙 (Japanese-first contrast)** — 서비스 전반(설명·해설·오답 피드백·UI 카피)에 일관 적용:
  > 한국어 규칙을 단독으로 서술하지 않는다. 항상 일본어와 대조해 **같은 점 → 다른 점 → 함정** 순으로 설명한다. "일본어 1개 → 한국어 여러 개"로 갈라지는 지점(조사·표현)은 역할 중심으로, 한자어는 한자 표기를 걸어 직관적으로.
- **제품 테제**: 콘텐츠 = 설명·순서(커리큘럼), 서비스 = **reps 엔진**(능동 풀이·즉시 채점·SRS 복습·진도 관리). EP 순서를 학습 경로로 삼는다.
- **스코프**: C층(망각·지속·아웃풋·수준파악·피드백·파편화) 집중. **범위 밖**: 발음·듣기 감각훈련(의도된 구멍), 실시간 회화, AI 첨삭.
- **레벨/지속성 방침**:
  - 레벨은 **가벼운 자기선택(can-do)**로 시작점만 잡고 진도 데이터가 보정. 하나의 밴드에 `우리 밴드 ↔ TOPIK 급수 ↔ 일본어 can-do 문장`을 묶어 호환.
  - 지속성은 **소프트·격려 톤, 죄책감 X, 러프한 목표**. 요일 고정 스케줄 대신 러프한 빈도 목표 + 휴식 있는 스트릭. **SRS due-큐가 일일 훅의 본체.**
- **어휘 데이터**(문법 편중 보완 축, 검증 완료 — 상세 `docs/todo.md`): 레벨 백본 = 2017 국제통용 6급 목록(공공누리1유형), 일본어 뜻+한자 = 한국어기초사전 krdict XML(초급 JP 100%, **CC-BY-SA** → 시드+재작성 or SA준수, 예문 미사용). 빌드는 미착수.
- **인프라**: `contexts/aws_deployment_context.md` 기준. AWS 서울, EC2 `t4g.small`(**ARM64**) + Docker Compose로 백엔드 + PostgreSQL, S3+CloudFront 프론트(`/api/*`→EC2), GitHub Actions(OIDC), 예산 $50/월. SSH·PostgreSQL 외부 노출 금지.

## 작업 원칙

- **착수 전 검증**: `docs/todo.md`에 잡힌 항목(예: 어휘 데이터 소스·라이선스)은 관련 기능 구현 전에 먼저 확인한다.
- **아이디어 구분**: "나중에 다룰 것" → `product_plan.md` Parking Lot / "착수 전 검증 필요" → `todo.md`.
- **정보 검색**: 로컬/한국 특화가 아니면 영어로 검색. 불확실하면 추측 대신 검색으로 보충 후 판단.
- **문서 동기화**: 방침·결정이 바뀌면 위 문서 맵의 해당 문서를 같은 턴에 갱신한다.
