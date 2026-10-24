# Local models

Results of running the brain on local models (Ollama) on an M1 Pro with 16 GB, 2026-10-24.

## Setup

A dedicated Ollama server, so the Ollama app's own server keeps its defaults:

```bash
sudo sysctl iogpu.wired_limit_mb=12288   # GPU may wire 12 GB instead of ~10.7; resets on reboot
OLLAMA_HOST=127.0.0.1:11435 OLLAMA_NUM_PARALLEL=4 OLLAMA_CONTEXT_LENGTH=32768 \
  OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 ollama serve
```

Ollama's default context is too short for a relevance batch of 25 paragraphs, and it truncates
without an error, hence `OLLAMA_CONTEXT_LENGTH`. Then from `brain/`:

```bash
BRAIN_LLM=local BRAIN_LOCAL_URL=http://localhost:11435/v1 BRAIN_LOCAL_MODEL=qwen3.5:9b \
BRAIN_LOCAL_VISION=1 BRAIN_LLM_TIMEOUT=3600 \
uv run python -m eval.suite --cases dev-rear-lamp --tag local-qwen3.5:9b-gated \
  --include "UN R148" "UN R48" "UN R150" "UN R10" \
  --exclude "UN R7" "UN R23" "UN R3" "UN R128" "UN R37" "UN R6"
uv run python -m eval.cached_relevance --since "2026-10-24 19:00"   # score a run mid-way
```

`--include` / `--exclude` fix the regulation list, as the Sunday review gate does, so a run
measures the paragraph steps. The model's own regulation picks are reported separately.

## qwen3.5:9b (thinking off)

Stopped after 69 of 113 relevance batches; no full-pipeline score.

- **Regulations:** picked R48, R148, R150 and the decoys R7, R23, R128, R37; missed R10. With
  thinking on, the review call ran past 12 minutes without an answer.
- **Paragraph relevance**, 1,692 dev paragraphs scored (92 in gold):

  | | n | gold | AUC qwen3.5:9b | AUC decision model (out of fold) |
  |---|---|---|---|---|
  | all | 1692 | 92 | 0.836 | 0.833 |
  | UN R48 | 1166 | 35 | 0.867 | 0.920 |
  | UN R148 | 374 | 40 | 0.767 | 0.849 |
  | UN R150 | 152 | 17 | 0.718 | 0.752 |

  It rates about half of all paragraphs as likely cited (p >= 0.5 keeps 730 of 1,692, recall
  0.92, precision 0.12). gpt-5.5 reached AUC 0.975 on the same task (README).
- **Speed:** 6.8 GB, fully on the GPU. About one relevance batch per minute (roughly 3,700
  prompt tokens each); a full dev run would take about 3 hours. Four parallel slots did not
  raise throughput, because the batches are mostly prompt reading, which is compute-bound.

## M5 with 16 GB, Ollama 0.40.10 (Vlad)

- The default `qwen3.5:9b` and `gemma4:12b` tags are NVFP4 builds on Ollama's MLX runner. They
  reject constrained JSON ("structured output is unavailable", HTTP 501) and default to
  temperature 1 with thinking on; `llm.py` falls back to prompted, validated JSON.
- With free memory, a cold relevance batch of 8 paragraphs took about 2 s per paragraph on
  qwen3.5:9b and 3 s on gemma4:12b, writing about 40 tokens/s. Under swap it was 3 to 6 times
  slower.
- `ollama ps` showed qwen3.5:9b reserving 16 GB at a 16k context, which pushed the Mac into
  swap. Close memory-heavy apps first, or use a smaller context or a GGUF build.
- Thinking on: one small batch took 90 to 100 s, and Qwen used its whole 3,000-token budget.

## Takeaways

- A 9B model with thinking off adds nothing over the decision model for relevance. Try a larger
  model (qwen3:14b fits with the 12 GB limit) or score yes/no per paragraph from token logprobs.
- Regulation review needs the strongest model available, or the human gate.
- Relevance reads every paragraph of the selected regulations; prefiltering by section or by the
  decision model's score is the main speed lever.
