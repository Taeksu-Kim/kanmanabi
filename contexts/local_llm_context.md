# Local LLM Context

로컬 개발 중 LLM이 필요할 때(설명·해설·오답 피드백 생성 등 실험) 쓰는 로컬 vLLM 서버 실행/접속 메모. **실측 검증 완료 (2026-08-09, RTX 4090 24GB, WSL2).**

## ⚠️ WSL 접속 함정 (제일 중요)

서버는 `0.0.0.0:8000`에 뜨지만 이 WSL 환경에서 **`127.0.0.1`/`localhost` 접속은 timeout으로 죽는다.** 반드시 **WSL IP `10.5.0.2`** 로 접속할 것.

```
127.0.0.1:8000     → FAIL (TimeoutError)
10.5.0.2:8000      → OK    ← 이걸 써라
```

(`agentic_rag/scripts/serve.sh`가 `WSL_IP=10.5.0.2`를 쓰던 이유. IP는 `hostname -I` 첫 값.)

## 사용 가능한 모델

| 모델 | 경로 | 용도 |
|------|------|------|
| Qwen3.5-9B-FP8-dynamic | `/mnt/d/workspace/stock dataset/models/Qwen3.5-9B-FP8-dynamic` | **기본** — 부팅·추론 빠름, 24GB에 여유 |
| Qwen3-30B-A3B-Instruct-2507-AWQ-4bit | `/mnt/d/workspace/custom_agent/model/Qwen3-30B-A3B-Instruct-2507-AWQ-4bit` | 더 큰 품질 필요할 때 (MoE, AWQ int4) |

- vLLM env: `~/miniconda3/envs/vllm` (conda)

## 실행 (9B — 기본)

```bash
VENV=$HOME/miniconda3/envs/vllm
CU=$VENV/lib/python3.12/site-packages/nvidia/cu13
export CUDA_HOME=$CU PATH=$CU/bin:$PATH LD_LIBRARY_PATH=$CU/lib:${LD_LIBRARY_PATH:-}
export VLLM_USE_FLASHINFER_SAMPLER=0 PYTHONUNBUFFERED=1

$VENV/bin/vllm serve "/mnt/d/workspace/stock dataset/models/Qwen3.5-9B-FP8-dynamic" \
  --served-model-name qwen35-9b --max-model-len 8192 --enforce-eager \
  --gpu-memory-utilization 0.72 --port 8000
```

- 부팅 ~2~3분. 로그에 `Application startup complete` 뜨면 준비 완료.
- 종료: `pkill -f '[v]llm serve'; pkill -9 -f 'VLLM::EngineCore'` (EngineCore 안 죽이면 좀비로 VRAM 물고 다음 부팅 방해).

### 대안: 30B AWQ
```bash
$VENV/bin/vllm serve "/mnt/d/workspace/custom_agent/model/Qwen3-30B-A3B-Instruct-2507-AWQ-4bit" \
  --quantization compressed-tensors --gpu-memory-utilization 0.85 \
  --max-model-len 2048 --trust-remote-code --port 8000
```

## 지금 떠 있는 서버로 바로 추론 (복붙용)

서버가 이미 `10.5.0.2:8000`에 떠 있는 상태에서 한 방에 쏘기.

**curl 한 줄:**
```bash
curl -s http://10.5.0.2:8000/v1/chat/completions -H "Content-Type: application/json" -d '{
  "model": "qwen35-9b",
  "messages": [{"role":"user","content":"안녕, 한국어로 짧게 인사해줘"}],
  "max_tokens": 512, "temperature": 0.3
}' | python3 -c "import sys,json;print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

**python 한 줄:**
```bash
python3 -c "import urllib.request,json;print(json.load(urllib.request.urlopen(urllib.request.Request('http://10.5.0.2:8000/v1/chat/completions',data=json.dumps({'model':'qwen35-9b','messages':[{'role':'user','content':'안녕, 한국어로 짧게 인사해줘'}],'max_tokens':512}).encode(),headers={'Content-Type':'application/json'})))['choices'][0]['message']['content'])"
```

## 접속 (OpenAI 호환 API)

```python
import json, urllib.request
base = "http://10.5.0.2:8000"          # ← 127.0.0.1 아님
body = json.dumps({
    "model": "qwen35-9b",
    "messages": [{"role": "user", "content": "..."}],
    "max_tokens": 512, "temperature": 0.3,
}).encode()
req = urllib.request.Request(base + "/v1/chat/completions",
                            data=body, headers={"Content-Type": "application/json"})
r = json.load(urllib.request.urlopen(req, timeout=120))
print(r["choices"][0]["message"]["content"])
```

- 모델 목록 확인: `GET http://10.5.0.2:8000/v1/models`
- 실측: 한국어 생성 정상, **~28 tok/s** (9B, enforce-eager).

## 주의점

- **9B는 답변 앞에 "Thinking Process"를 뱉는 경향** → `max_tokens`를 넉넉히(≥512) 주거나 system 프롬프트로 사고 과정 억제. 짧게 캡 걸면 생각만 하다 잘린다.
- 참고 원천: `agentic_rag/scripts/serve.sh` (풀 서빙 스택 런북 — 임베더·리랭커 포함), `custom_agent/README.md` (30B AWQ 커맨드).
