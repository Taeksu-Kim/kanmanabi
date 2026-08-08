# korean_helper — 프로젝트 개요

> 큰 맥락과 현재 시스템 정리. 상세 구현 방향은 이후 문서에서 다룬다.
> 이 문서는 CLAUDE.md·설계 문서의 기반이 되는 최상위 컨텍스트다.

## 한 줄 정의

한국어를 공부하는 **일본인 학습자를 보조하는 웹서비스**. 이미 구축된 콘텐츠 자산(`kr_study_material`)을 웹 학습 경험으로 재활용한다.

## 두 개의 자산

### 1. `kr_study_material` — 콘텐츠 원천 (별도 repo, 이미 운영 중)

일본인 대상 한국어 문법 블로그(https://kankokugots.blogspot.com/)를 YouTube 강의 영상으로 제작하는 파이프라인.

- **소스**: `docs/source/` — 블로그 원문 스크랩 88챕터. 일본어로 한국어 문법 설명 (예문·표·연습문제·정답 포함, 읽기 전용)
- **산출물**: `docs/episodes/EP01~EP42` — 42편 완성. EP마다 `episode.md`(재구성 콘텐츠) → Marp 슬라이드(PNG) → TTS 스크립트 → 음성 → mp4 → YouTube 설명란 → 업로드
- **커버 범위**: 지시어 → 조사 → 활용 → 과거형 → 경어 → 미래·진행·부정 → 연결어미 등 **입문자용 한국어 문법 코스 전체**가 EP 단위로 구조화됨
- 웹서비스 입장에서는 **정제된 학습 콘텐츠 + 영상 + 연습문제/정답의 창고**

경로: `/mnt/d/workspace/kr_study_material` (상세는 해당 repo의 `CLAUDE.md` 참조)

### 2. `korean_helper` — 이 repo (학습 웹서비스, 신규)

- 현재 상태: `contexts/aws_deployment_context.md`(인프라 설계) + `docs/`(이 문서) 만 존재. 코드 없음.
- 역할: `kr_study_material`의 콘텐츠를 소비해 **웹에서 상호작용형 학습 경험**을 제공

## 큰 맥락

```
[콘텐츠 생산]  kr_study_material  →  블로그 → EP 콘텐츠/영상/연습문제  (YouTube 배포)
                     │
                     │  (같은 콘텐츠를 재활용)
                     ▼
[학습 서비스]  korean_helper      →  웹에서 일본인 학습자를 보조
                                      = 영상 + 문법 + 연습문제를 상호작용 + 진도 추적
```

콘텐츠를 새로 만드는 게 아니라, **있는 것을 학습 도구로 변환하는 레이어**가 핵심.

## 확정된 결정

- **사용자별 상태 저장 필요** → PostgreSQL 사용 확정. 계정/로그인, 학습 진도, 정답률 등 stateful 기능이 서비스 범위에 포함됨. (단순 정적 사이트 아님)
- **인프라 방향**: `contexts/aws_deployment_context.md` 기준
  - AWS 서울(`ap-northeast-2`), EC2 `t4g.small`(ARM64) + Docker Compose로 백엔드 + PostgreSQL
  - S3 + CloudFront로 프론트, `/api/*`는 EC2 백엔드로 라우팅 (프론트는 상대경로 `/api/...` 호출)
  - CI/CD는 GitHub Actions(OIDC), 예산 $50/월, **ARM64(linux/arm64) 이미지 필수**
  - 제약: SSH·PostgreSQL 외부 노출 금지, 유료 AWS 서비스 최소화
- **어휘 데이터 소스 확정** (상세 [`todo.md`](./todo.md)): 문법 편중을 보완할 어휘 축. 레벨 백본 = 국립국어원 2017 국제통용 6급 목록(공공누리1유형), 일본어 뜻·한자 = 한국어기초사전 krdict XML(초급 JP 100% 실측, CC-BY-SA). 취약점(단어)의 소스·실현성 검증 완료 — 남은 건 빌드.

## 아직 정하지 않은 것 (이후 논의)

- "보조"의 구체 기능 범위 → 대체로 확정됨: reps 엔진(능동 풀이·즉시 채점·SRS·진도) on EP 학습경로. 상세 [`product_plan.md`](./product_plan.md). MVP 최소 루프만 미확정.
- 콘텐츠 반입 방식: `kr_study_material` 산출물 + 어휘 마스터를 어떻게 DB/서비스로 가져올지 (동기화 vs 빌드타임 임포트)
- 기술 스택(백엔드 프레임워크·프론트 프레임워크) 구체 선정
- 데이터 모델 (EP·문법포인트·문제·어휘·사용자진도·복습큐 스키마)
```
