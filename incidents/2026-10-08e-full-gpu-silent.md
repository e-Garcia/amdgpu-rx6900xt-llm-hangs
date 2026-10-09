# Incident 6: 2026-10-08 21:55, silent hang with all weights on the GPU

The first hang **without any CPU offload**. GFXOFF still disabled (`ppfeaturemask=0xffff7fff`, as in incident 5).

**Config:** Qwen3.6-35B-A3B UD-Q2_K_XL + `mmproj-F16`, `-ngl 999 --n-cpu-moe 0 -fa on -ctk q8_0 -ctv q8_0 -c 163840 -np 1
--jinja --threads 16`, 15.50 GB VRAM (97 %). Same llama.cpp source build as incidents 2–5.

**Workload before the hang** (one server process, loaded 21:27):
- 18 agent tasks through an agent framework (short prompts, tool calls, idle gaps), 21:27–21:47: no problem.
- Long-prompt recall ladder, fresh documents: 4.5K, 17K, 34K, 67K, 100K tokens: all passed.
- Next read (~117K tokens): **hung ~76K tokens in**, prompt reading on the GPU at ~1140 tok/s.

**Logs:**
- llama-server's last progress line 21:55:40 (`n_tokens = 75776, progress = 0.65`):
  [../logs/llama-server-prefill-before-hang6.txt](../logs/llama-server-prefill-before-hang6.txt).
- The 30 s GPU monitor logged VRAM at 21:55:55 but never logged the temperature read that follows (the sysfs read
  did not return). Temps before: 55–65 °C: [../logs/gpu-monitor-before-hang6.txt](../logs/gpu-monitor-before-hang6.txt).
- Last journal line 21:55:57. **No amdgpu / SMU / AER / MCE message**:
  [../logs/boot-2026-10-08e-last-lines.txt](../logs/boot-2026-10-08e-last-lines.txt).
- The host reset itself 43 s later (as after every hang here). The card was **absent from PCI** for that whole boot:
  [../logs/boot-2026-10-08f-card-absent.txt](../logs/boot-2026-10-08f-card-absent.txt). AC power cycle the next morning
  restored it.

**What it changes:** "only offloaded prompt reads hang" is no longer true. Full-GPU reads hung 0 times in dozens of runs
with GFXOFF **on**, and hung after ~5 reads with GFXOFF **off**. Either disabling GFXOFF made things worse, or full-GPU
prefill hits the same fault at a lower rate. See [../findings/pattern.md](../findings/pattern.md).
