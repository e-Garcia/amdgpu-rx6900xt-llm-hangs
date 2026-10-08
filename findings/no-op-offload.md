# Test 6: `--no-op-offload` (no hang; soak passed)

**Hypothesis:** the trigger is the host→GPU weight streaming that llama.cpp does while reading prompts with
`--n-cpu-moe`. For large batches (prompt chunks of `-ub` 512 tokens), the scheduler "offloads" operations of CPU-resident
expert layers to the GPU by copying those layers' expert weights over PCIe for **every chunk**: several GB of DMA per
chunk, alternating with GPU compute bursts. Generation (small batches) and full-GPU runs don't do this, and neither
ever hung. `--no-op-offload` makes the CPU compute those layers itself, so no weights are streamed.

**Setup:**
- Clean boot after an AC power cycle.
- GFXOFF still disabled from mitigation #2 (`ppfeaturemask=0xffff7fff`).
- Same config as incidents 2–5, plus `--no-op-offload`.

**Results** (every request passed all checks: recall 10/10, corrected facts 3/3, 0 hallucinations, vision 2/2):

| Prompt (fresh document) | Prompt read | Cumulative offloaded prompt tokens |
|---|---|---|
| 5K | 441 tok/s | 5K |
| 67K | 522 tok/s | 72K |
| 136K | 512 tok/s | 208K |
| 173K | 468 tok/s | 381K (incident 5 hung after ~330K) |
| 105K | 558 tok/s | 485K |
| 157K | 485 tok/s | 642K |
| 193K | 446 tok/s | **835K, no hang** |

**Cost:** prompt reading runs at ~470–560 tok/s instead of ~730–1060 tok/s with op-offload. Generation speed is unchanged.

**Open:**
- Is `--no-op-offload` sufficient with GFXOFF re-enabled? Incident 4 showed AllowGfxOff as a second trigger.
- Does a smaller `-ub` with op-offload on (smaller DMA bursts) also avoid it?

Reproduce: `repro/serve.sh 204800 8 --no-op-offload` (extra args are passed to llama-server).
