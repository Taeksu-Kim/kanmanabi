# Vector DB Context

벡터검색 스택(임베딩 모델 + Qdrant) 실행/사용 메모. 원천은 `agentic_rag`(법령 RAG)에서 검증된 구성. **korean_helper는 기존 데이터와 섞지 않고 별도 collection에 신규 벡터만 넣는다.**

참고: 로컬 LLM(생성용) 서버는 [`local_llm_context.md`](local_llm_context.md). WSL 접속 함정(`127.0.0.1` 죽음 → `10.5.0.2` 사용)은 여기도 동일하게 적용된다.

## 임베딩 모델

| 항목 | 값 |
|------|-----|
| 모델 | **Qwen3-Embedding-0.6B** (HF repo id `Qwen/Qwen3-Embedding-0.6B`) |
| 차원 | **1024** |
| 거리 | **COSINE** |
| API | OpenAI 호환 `/v1/embeddings` (`{"model", "input":[...]}`) |
| 리랭커(선택) | Qwen3-Reranker-0.6B — 2단계 크로스인코더. 정밀도 필요할 때만. |

## 임베더 vLLM 실행

```bash
VENV=$HOME/miniconda3/envs/vllm
CU=$VENV/lib/python3.12/site-packages/nvidia/cu13
export CUDA_HOME=$CU PATH=$CU/bin:$PATH LD_LIBRARY_PATH=$CU/lib:${LD_LIBRARY_PATH:-}
export VLLM_USE_FLASHINFER_SAMPLER=0 PYTHONUNBUFFERED=1

$VENV/bin/vllm serve Qwen/Qwen3-Embedding-0.6B --runner pooling \
  --served-model-name qwen3-emb --max-model-len 4096 \
  --gpu-memory-utilization 0.10 --kv-cache-memory-bytes 536870912 --port 8001
```

- `--runner pooling` 필수 (생성이 아니라 임베딩 pooling 모드).
- VRAM ~1GB 남짓. 생성용 LLM과 동시 상주 가능하지만, 24GB에서 3모델 동시엔 기동 순서/util 주의 (상세 런북: `agentic_rag/scripts/serve.sh`).
- 종료: `pkill -f '[v]llm serve'; pkill -9 -f 'VLLM::EngineCore'`

### 리랭커(선택)
```bash
$VENV/bin/vllm serve Qwen/Qwen3-Reranker-0.6B --runner pooling \
  --served-model-name qwen3-reranker --max-model-len 2048 \
  --gpu-memory-utilization 0.12 --port 8002 \
  --hf-overrides '{"architectures":["Qwen3ForSequenceClassification"],"classifier_from_token":["no","yes"],"is_original_qwen3_reranker":true}'
```
공식 채팅 템플릿 없이는 순위가 무의미해지는 것 실측됨 → `/score` + 템플릿 사용.

## Qdrant — 분리된 공간(collection)

**격리 단위 = collection.** 같은 Qdrant 서버(`:6333`)에 컬렉션 이름만 다르게 만들면 기존 데이터(`agentic_rag`의 `statutes`)와 완전 격리 — 포인트도 검색도 안 섞인다. 서버/포트는 그대로.

Qdrant 기동(native, agentic_rag와 공유): `QDRANT__STORAGE__STORAGE_PATH=$HOME/qdrant_storage $HOME/qdrant/qdrant`

```python
from qdrant_client import QdrantClient, models
import requests

client = QdrantClient(url="http://localhost:6333")
EMB = "http://10.5.0.2:8001/v1"          # ← 127.0.0.1 아님 (WSL)
COLL = "kh_vocab"                         # korean_helper 전용 = 분리된 공간

# 1) 컬렉션 생성 (한 번만). 순수 dense — agentic_rag의 named+sparse 하이브리드는 불필요.
if not client.collection_exists(COLL):
    client.create_collection(
        collection_name=COLL,
        vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
    )

def embed(texts):
    r = requests.post(f"{EMB}/embeddings",
                      json={"model": "qwen3-emb", "input": texts}, timeout=120)
    return [d["embedding"] for d in r.json()["data"]]

# 2) 신규 벡터 upsert
words = [{"id": 1, "word": "학교", "ja": "学校"}]
vecs = embed([w["word"] for w in words])
client.upsert(COLL, points=[
    models.PointStruct(id=w["id"], vector=v, payload=w)
    for w, v in zip(words, vecs)
])

# 3) 검색 — 이 컬렉션 안에서만
qvec = embed(["학교"])[0]
hits = client.query_points(COLL, query=qvec, limit=5).points
for h in hits:
    print(h.score, h.payload)
```

**핵심**
- 새 공간 = `create_collection`에 새 이름. 기존 데이터 안 건드림.
- 통째로 리셋: `client.delete_collection("kh_vocab")` → 그 컬렉션만 삭제.
- dim(1024)·distance(COSINE)는 임베딩 모델에 맞춘 값. 모델 바꾸면 같이 바꿔야 함.
