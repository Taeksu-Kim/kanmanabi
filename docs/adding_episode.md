# 새 EP 추가 가이드

> 새 강의 영상(EP44~)을 서비스에 반영하는 절차. **콘텐츠 제작은
> `kr_study_material`(별도 repo), 문제 생성·적재는 이 repo**에서 한다.
> 배포 인프라는 [`deployment.md`](./deployment.md), 유형 분류는 [`ep_grammar_map.md`](./ep_grammar_map.md).

## 전체 흐름

```text
kr_study_material                    korean_helper (이 repo)
─────────────────                    ───────────────────────
1. 영상·episode.md 제작
2. video_plan.md에 EP44 행 추가
                          ────────▶  3. data/episode_videos.json 에 YouTube ID
                                     4. 문제 생성 (유형별, 아래 §2)
                                     5. bash scripts/push_data.sh EP44
                                            ↓
                                     서비스에 즉시 반영 (배포 불필요)
```

**코드 배포는 필요 없다.** 서버는 `data/*.json`을 읽지 않고 DB만 보며, EP 개수도
하드코딩이 아니라 `len(episodes)`로 계산한다. 프론트도 API에서 받는다.

---

## 1. 준비 (§3~5 전에)

| 파일 | 내용 |
|---|---|
| `kr_study_material/video_plan.md` | `\| EP44 \| 제목 \| ch68 \| ... \|` 행 추가 — seed가 여기서 EP 메타를 파싱한다 |
| `data/episode_videos.json` | `"EP44": "<11자 YouTube ID>"` 추가 (URL이 아니라 ID만) |

---

## 2. 문제 생성 — 유형부터 판단한다

새 EP의 문법 포인트가 어느 유형인지 먼저 정한다. 작업량과 비용이 완전히 다르다.

| 유형 | 대상 | 엔진 | 토큰 | 사람 검토 |
|---|---|---|---|---|
| **T1** 조사·형태 | 받침으로 답이 결정됨 (이/가, 을/를, (으)로) | 로직만 | 0 | 불필요 |
| **T2** 활용 | 어미 변화 (과거·경어·관형형) | 로직만 | 0 | 불필요 |
| **T3** 의미·뉘앙스 | 문맥으로 골라야 함 (-고 vs -아서) | **luna** | 발생 | **필수** |

> 초급 문법(EP01~43)은 T1·T2가 많았지만, **EP44 이후 새 문법은 대부분 T3**가 된다.
> 형태로 결정되는 규칙은 이미 대부분 다뤘기 때문이다.

### T1 — 조사·형태 (`scripts/gen_grammar.py`)

`EP_PARTICLES`에 EP와 조사 qtype을 매핑한다.

```python
EP_PARTICLES = {
    "EP44": ["particle_reul"],       # 기존 조사를 재사용하는 경우
}
```

**새로운 조사**라면 `PARTICLE`에 판정 함수를 추가한다. 받침 유무로 갈리는 쌍이면
`_pair()` 한 줄이면 된다:

```python
PARTICLE = {
    "particle_wa": ("「~と」", _pair("과", "와")),   # 받침 있으면 과, 없으면 와
}
```

예외가 있는 조사는 `_ro()`처럼 별도 함수로 짠다(ㄹ받침은 `으로`가 아니라 `로`).

실행: `python scripts/gen_grammar.py --levels 1,2`

### T2 — 활용 (`scripts/gen_conjug.py`)

`FORMS`에 한 줄 추가한다. 네 번째 항목이 정답을 계산하는 엔진 함수다.

```python
FORMS = [
    ("EP44", "some_form", "ラベル(日本語)", lambda e: c.some_form(e["word"])),
]
```

엔진에 그 활용이 없으면 `scripts/conjug.py`에 먼저 구현한다.
**불규칙(ㄷ/ㅂ/ㅅ/ㅎ/르)은 `scripts/irregular.py` 분류표를 참조**하므로,
새 어휘가 불규칙이면 거기에 등록해야 한다. 미등록 단어는 안전하게 제외된다
(틀린 답을 가르치지 않기 위함).

오답은 학습자가 실제로 저지르는 실수로 만든다 — 모음조화 뒤집기, 으 토글, ㅡ 미탈락 등.

실행: `python scripts/gen_conjug.py --levels 1,2`

### T3 — 뉘앙스 (`scripts/gen_nuance.py`) ← 새 EP는 대부분 여기

`SPECS`에 EP 항목을 쓴다. **이게 luna에게 주는 프롬프트다.**

```python
"EP44": {
    "qtype": "nuance_xxx",          # 48종과 겹치지 않게. 40자 이내
    "gate": "light",                # 은/는·이/가류 형태검증이 필요하면 "form"
    "rule": "…의 문법 설명 (일본어)",
    "constraint": "…문제 형식 제약 (일본어)",
    "choices_hint": "선택지 예시",
},
```

**세 필드를 쓰는 요령** (오늘 21개 EP를 만들며 정리한 것):

- **`rule`** — 문법 설명 + **일본어와 어디서 헷갈리는지**를 반드시 넣는다.
  `docs/project_overview.md`의 Japanese-first 원칙이 여기서 지켜진다.
  > 예: `「-고」(単純な並列)と「-아/어서」(原因)の違い。両方日本語では「〜て」になり混同しやすい`

- **`constraint`** — 형식을 못 박는다. 안 쓰면 형식이 깨진 문제가 대량으로 나온다.
  - `空所は各問ちょうど1つ、必ず ( ) の形で書く`
  - `1問の中で複数の文法項目を混ぜない`
  - `選択肢は同じグループ内のものだけを並べる`

- **`choices_hint`** — 선택지 후보. **서로 배타적인 것만** 넣는다.
  `아주`와 `정말`처럼 바꿔 써도 되는 걸 같이 넣으면 복수정답이 된다.

생성 → 검토 → 승인:

```bash
python scripts/gen_nuance.py --ep EP44                      # 생성(캐시), 출력 검토
python scripts/gen_nuance.py --ep EP44 --approve --reject 3,7   # 반려 빼고 승인
python scripts/gen_nuance.py --ep EP44 --force              # 프롬프트 고쳐 재생성(토큰 발생)
```

승인 전에는 `needs_review=True`라 **서빙되지 않는다.** 캐시가 있어 재실행은 토큰 0.

---

## 3. 검토 기준 — luna는 20%쯤 틀린다

승인 전 반드시 사람이 본다. **실제로 반려했던 패턴**:

| 패턴 | 예 |
|---|---|
| 문제문에 정답 노출 | `네, ( ).` → 답이 `네` |
| 빈칸 앞뒤 중복 | `먹어 보( )` + 답 `봤어요` → "보봤어요" |
| 관형형 중복 | `온( )` + 답 `ㄴ 거 아니에요` |
| 어간 절단 | `요리( )` + 답 `는구나` → 어간은 `요리하` |
| 복수정답 | 선택지에 `아주`와 `정말`이 함께 |
| 해설이 정답과 모순 | 답은 `게`인데 해설은 "히가 자연스럽다" |
| 문맥 오류 | "매일 한국어를 공부 못 해요" |

반려가 많아 문항이 얇아지면 `--force`로 프롬프트를 고쳐 재생성한다.
**반려율이 높다는 건 `constraint`가 부족하다는 신호다.**

---

## 4. 데이터 포맷

생성기가 만드는 문항 JSON (`data/questions_*.json`, `data/nuance/EP44.json`):

```jsonc
{
  "qtype": "nuance_go_seo",          // 40자 이내. DB 컬럼 제한
  "ep_no": "EP44",                   // seed가 episode_id로 해석
  "prompt": "밥을 먹( ) 학교에 가요.",
  "answer": "고",
  "choices": ["고", "어서"],          // 2~4개. 빈 배열이면 주관식
  "difficulty": 3,                   // 1=형태 / 2=규칙 / 3=의미판단
  "source": "authored",              // generated(로직) | authored(luna)
  "level": 1,
  "explanation": "…(일본어 해설)",     // 필수. 일본어 대조가 원칙
  "needs_review": false,             // true면 서빙 제외
  "vocab_key": { "word": null, "homonym_no": null, "pos": null }
}
```

- **`vocab_key`**: 특정 어휘에 매달린 문제면 채우고(→ `vocab_id` 연결),
  EP 문법 문제면 `null`. **둘 중 하나는 반드시 있어야** 출제된다.
- **`explanation`은 비우지 않는다.** 일본어 대조 해설이 이 서비스의 핵심이다.

---

## 5. 운영 DB 적재

```bash
bash scripts/push_data.sh EP44          # SSH 터널 + 증분 적재를 한 번에
bash scripts/push_data.sh --check       # 적재 없이 현재 상태만 확인
```

- **`--rebuild`는 쓰지 않는다.** questions id가 재발급되어 유저 SRS 진도가 무효화되고,
  진도가 있으면 FK 때문에 실패한다. 초기 구축 전용이며 확인 프롬프트가 붙어 있다.
- 증분 적재는 그 EP 문항만 교체하고 딸린 카드·이력도 정리한다(orphan 방지).

적재가 끝나면 **재배포 없이 즉시** `/learn/grammar`에 EP44가 나타난다.

---

## 6. 예외 — 프론트 배포가 필요한 경우

지금까지 없던 `qtype`을 만들면 프론트가 그 유형의 라벨을 모른다.
동작은 한다(중립 라벨 `正しい答えは？`로 폴백). 유형에 맞는 안내 문구를 넣으려면
그때만 `frontend/src/features/study/studySession.ts`를 손보고 배포한다.

기존 유형을 재사용하면 **완전히 데이터만으로** 끝난다.

---

## 7. `kr_study_material`에서 참조하기

스크립트는 이 repo의 `seed.py`·`backend/app` 모델에 의존하므로 **밖으로 복사하지 않는다.**
콘텐츠 repo에서는 경로만 참조한다:

```bash
cd /mnt/d/workspace/korean_helper
bash scripts/push_data.sh EP44
```
