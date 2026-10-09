# `--no-op-offload` (tests 6–7: no hang)

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

## Test 7: heavy offload (`--n-cpu-moe 46`, 125B-A6B MoE) with `--no-op-offload`

The service that hung on 2026-09-30 (at ~56K tokens into a prompt read, op-offload on) was re-tested with
`--no-op-offload`. Text-only fresh prompts, GFXOFF still disabled, all checks passed every time:

| Prompt (fresh) | Prompt read | Time to first token | Generation |
|---|---|---|---|
| 5K | 33 tok/s (startup-dominated) | 150 s | 16.2 tok/s |
| 30K | 85 tok/s | 5.8 min | 16.4 tok/s |
| 59K | 82 tok/s | 12.0 min | 16.0 tok/s |
| 99K | 78.5 tok/s | 21.1 min | 14.8 tok/s |
| 136K | 76.5 tok/s | 29.6 min | 13.8 tok/s |

~330K offloaded prompt tokens, **no hang**. Cost: prompt reading ~2.5× slower than with op-offload (~195 tok/s), because
with most experts on the CPU the CPU does all expert work for prompt chunks. Generation speed is unchanged.
