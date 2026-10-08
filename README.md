# RX 6900 XT (Navi 21) hard hangs during LLM inference with CPU-offloaded MoE experts

Public, scrubbed incident log and reproduction kit for a recurring **AMD GPU SMU failure that takes the
whole Linux host down** while llama.cpp (HIP/ROCm) reads a long prompt with Mixture-of-Experts weights
partly offloaded to the CPU (`--n-cpu-moe N`). After each hang the card **disappears from the PCI bus** until an
AC power cycle (`reboot` is not enough).

**Status:** open, root cause unconfirmed. 3 incidents (2026-09-30, 2026-10-08 ×2). Mitigations not yet tested
([findings/mitigations.md](findings/mitigations.md)).

## Signature

```
amdgpu 0000:09:00.0: amdgpu: SMU: I'm not done with your previous command: SMN_C2PMSG_66:0x00000012 SMN_C2PMSG_82:0x00000005
amdgpu 0000:09:00.0: amdgpu: Failed to export SMU metrics table!
```
…then nothing else is logged, the host freezes or resets, and on the next boot `lspci` no longer lists the GPU.
At every boot: `smu driver if version = 0x00000040, smu fw if version = 0x00000041 ... (58.89.0)`.

## The pattern so far

| # | Date | Workload at the hang | Prompt tokens read when it hung |
|---|---|---|---|
| 1 | 2026-09-30 | Qwen3.8-Flash-Next 125B-A6B, `--n-cpu-moe 46`, ~200 tok/s | ~56K |
| 2 | 2026-10-08 11:05 | Qwen3.6-35B-A3B Q2 + vision, `--n-cpu-moe 8` | 67K-prompt request (no SMU line captured) |
| 3 | 2026-10-08 12:13 | same as #2, clean boot | ~90K of 136K |
| 4 | 2026-10-08 15:33 | same, clocks pinned `high`; first stuck SMU msg `0x28` AllowGfxOff | early in a 67K prompt |
| 5 | 2026-10-08 16:36 | same, GFXOFF disabled (`ppfeaturemask=0xffff7fff`); silent, no SMU line | ~105K of 172K, after ~330K offloaded tokens passed |

**Never hung:** dozens of long prompts read **fully on the GPU** (no `--n-cpu-moe`), up to 198K tokens
(Qwen3.6) and 247K (Bonsai 27B), the same day, on the same host and driver. Short offloaded requests were also fine.
Details in [findings/pattern.md](findings/pattern.md).

## Repo layout

| Path | What |
|---|---|
| [HARDWARE-SOFTWARE.md](HARDWARE-SOFTWARE.md) | Exact hardware, kernel, firmware, ROCm and llama.cpp versions |
| [incidents/](incidents/) | One file per incident: timeline, logs, what was ruled out |
| [logs/](logs/) | Redacted text excerpts (kernel amdgpu lines, GPU temp/VRAM samples, llama-server progress) |
| [findings/](findings/) | Pattern analysis, mitigation matrix, a separate PrismML-prebuilt GPU fault |
| [repro/](repro/) | Scripts to reproduce: server launcher, long-prompt generator/tester, environment collector |
| [tools/](tools/) | `redact.sh` and `pii-check.sh`. Every log is passed through redaction, and CI runs the check |
| [PRIVACY.md](PRIVACY.md) | What may and may not be committed |

## Current best workaround

Add **`--no-op-offload`** to llama-server whenever you use `--n-cpu-moe` / `-ot` CPU offload on this card. With it, the
same config read 485K+ tokens of fresh long prompts without a hang (soak ongoing), against 5/5 hangs without it, at
about half the prompt-read speed. Details: [findings/no-op-offload.md](findings/no-op-offload.md).

## If you have a Navi 21 card

Run `repro/collect-env.sh` and open an issue with its output. Try `repro/` with and without `--n-cpu-moe`.
**Warning:** a successful repro hangs the host and needs a power cycle. Save your work first.

## Upstream

Candidates to report to: [drm/amd on freedesktop GitLab](https://gitlab.freedesktop.org/drm/amd/-/issues)
(kernel/SMU), [ROCm](https://github.com/ROCm/ROCm/issues), [llama.cpp](https://github.com/ggml-org/llama.cpp/issues).

License: MIT (scripts) / CC BY 4.0 (docs).
