# Pattern: hangs happen during long prompt reading, mostly with MoE experts on the CPU

| Condition | Long-prompt runs | Hangs |
|---|---|---|
| All weights on GPU (`--n-cpu-moe 0`), GFXOFF on | dozens: 4K–198K (Qwen3.6-35B-A3B Q2 + vision, 2 builds), up to 247K (Bonsai 27B ternary) | 0 |
| All weights on GPU, GFXOFF off (`0xffff7fff`) | agent tasks + 5 reads up to 100K, then a ~117K read | **1** (incident 6, silent) |
| Experts on CPU with `--no-op-offload`, GFXOFF off | ~1.17M prompt tokens, reads up to 193K, two models | 0 |
| MoE experts partly on CPU, short prompts (≤5K) | several | 0 |
| MoE experts partly on CPU, long prompts (≥56K) | 4 | **3** (the only one that passed was a 67K-token read) |

**Hypothesis (unproven):** with experts on the CPU, the GPU alternates between compute bursts and waits
on host-side expert compute and PCIe transfers. That drives rapid DPM / GFXOFF power-state transitions. Given
the SMU driver/firmware interface mismatch (0x40 vs 0x41), the SMU eventually stops answering a
`TransferTableSmu2Dram` (metrics) request, and the device falls off the bus.

The amdgpu driver periodically requests the metrics table itself (sensors / `gpu_metrics`). A userspace
monitor also polled `rocm-smi` every 30 s on this host. Whether polling frequency matters is untested.

## Update after incident 6 (full GPU)

Incident 6 hung with nothing on the CPU, so CPU offload is not required. Current reading:

1. **One fault whose rate scales with sustained heavy GPU work plus PCIe traffic.** Offload with op-offload (bursty GPU,
   GBs of weight DMA per chunk) hit it within ~60–330K tokens; full-GPU prefill much more rarely. `--no-op-offload` keeps
   the GPU mostly idle during prompt reads (5 s sysfs trace on the 125B run: avg 67 W, 17 % busy), which may be why it
   looked like a fix. Counter-point: one `--no-op-offload` soak averaged 181 W / 72 % busy and passed.
2. **Disabling GFXOFF changed or worsened it.** Both GFXOFF-off hangs were silent (no SMU message), and full GPU only hung
   after the change. One data point. A community report found `0xffff7fff` did not help but `0xfff73fff` (also clears
   OVERDRIVE `0x4000` and GFX_DCS `0x80000`) did: https://forum.endeavouros.com/t/random-crashes-amdgpu/70453/15
3. **Power transients** (6900 XT transients far above the 289 W software reading:
   https://www.igorslab.de/en/grasps-at-the-crown-radeon-rx-6900-xt-16-gb-in-test-with-benchmarks-and-a-technology-analysis/15/).
   Less likely: the host resets rather than powering off, and temperatures were normal.

Similar report: https://gitlab.freedesktop.org/drm/amd/-/issues/2756 (RX 6800 XT, ROCm workloads → crash, reboot, card
unusable until a full power-off, SMU errors).
