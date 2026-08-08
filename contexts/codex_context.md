# Codex (gpt-5.6-luna) Inference Context

로컬 개발 중 **프런티어급 LLM 추론**이 필요할 때 쓰는 Codex CLI 메모.
로컬 vLLM 9B([`local_llm_context.md`](./local_llm_context.md))보다 품질이 높아 **소프트 생성**(예문·해설·뉘앙스)에 적합.
단, 사실 판정(받침·조사·정답)은 여전히 **로직 전담** — LLM 출력은 항상 검증 대상.

## 전제

- `codex-cli` 설치·로그인 완료 (`codex --version`, `codex doctor`).
- 기본 모델: `gpt-5.6-terra` (effort `high`) — `~/.codex/config.toml`. 이 문서는 `gpt-5.6-luna` 사용.
- reasoning effort 지원값: `none` · `low` · `medium` · `high` · `xhigh` · `max`
  - ⚠️ luna는 `minimal` **미지원** — 최하는 `none`.

## 비대화 추론 (복붙용)

프롬프트를 stdin(또는 파일)으로 주고 JSON만 받기:

```bash
codex exec -m gpt-5.6-luna -c model_reasoning_effort="none" \
  -s read-only --skip-git-repo-check --ephemeral -C . - < prompt.txt
```

- `-` + stdin 파이프 → 프롬프트를 stdin에서 읽음 (인자로 줘도 됨)
- `-s read-only` : 모델이 쉘을 쓰려 해도 쓰기 차단 (순수 Q&A엔 도구 안 씀)
- `--ephemeral` : 세션 파일 미저장
- `-C <dir>` : 작업 루트, `--skip-git-repo-check` : git repo 밖 허용
- 결과는 **stdout에 최종 메시지만**. `tokens used` 등은 stderr.
- **구조화 강제**: `--output-schema <schema.json>` — JSON Schema로 응답 형태 고정 (배치 파이프라인 권장).

경고 `bubblewrap not found on PATH` → 무해(번들 bubblewrap 사용).

## 실측 (2026-08-09, 받침/조사 20단어)

| 엔진 | 정확도 | 속도 |
|------|--------|------|
| **gpt-5.6-luna (effort=none)** | **20/20 (100%)** | 8.8s |
| 로컬 Qwen 9B (한국어 프롬프트) | 13/20 (65%) | ~13s |
| 로컬 9B (few-shot + 띵크 ON) | 무한루프 붕괴 | — |
| 우리 로직 (유니코드 분해) | 100% | 즉시 |

## 역할 경계 (문제 생성)

- **로직** — 받침·조사·정답·오답후보·등급필터·채점. 무료·즉시·보장. **luna가 100%여도 받침류는 로직 유지**(비용·보장 이유, 표본 100%≠전량 보장).
- **Codex(luna)** — 로직이 못 하는 **소프트 생성**(예문·뉘앙스 은/는vs이/가·해설). 오프라인 배치 + `--output-schema`.
- **로컬 9B** — 비용 민감 초안용(품질 낮음, 무거운 검증 필요).
- ⚠️ **프런티어여도 자모·뉘앙스 해설이 틀릴 수 있음** → 출력은 로직/사람 검증 후 사용. LLM에 사실을 *묻지* 말고, 로직이 계산한 사실을 *주고* 표현만 시킨다.
