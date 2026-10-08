# Incident 5: 2026-10-08 ~16:36, silent hang with GFXOFF disabled

Mitigation #2 test: AC power cycle, boot with `options amdgpu ppfeaturemask=0xffff7fff` (`pp_features`:
`GFXOFF: disabled`), DPM `auto`. Same config as incidents 2–4 (Qwen3.6-35B-A3B Q2 + mmproj, 200K q8_0 KV, `--n-cpu-moe 8`).

| Prompt | Prompt read | Result |
|---|---|---|
| 5K | 1062 tok/s | pass |
| 67K | 977 tok/s | pass (incident 4 hung early in this read) |
| 136K | 728 tok/s, 188 s | pass (incident 3 hung at ~90K of this read) |
| 125K, fresh document | 756 tok/s, 166 s | pass |
| 172K, fresh document | ~830 tok/s | **hung at 104,672 tokens (61 %), ~126 s in** |

- **Kernel log:** nothing; no SMU line this time (as in incident 2). Last journal line 16:36:43, reset, GPU absent from `lspci`.
- **Result:** GFXOFF off let the card get through ~330K tokens of offloaded prompt reading before hanging, against 67–90K
  in incidents 2–4. It may remove one trigger, but it does **not** prevent the hang.
- Logs: [../logs/boot-2026-10-08d-last-lines.txt](../logs/boot-2026-10-08d-last-lines.txt),
  [../logs/llama-server-prefill-before-hang5.txt](../logs/llama-server-prefill-before-hang5.txt),
  [../logs/gpu-trace-gfxoff-disabled-2026-10-08d.txt](../logs/gpu-trace-gfxoff-disabled-2026-10-08d.txt) (covers the passing steps only)
