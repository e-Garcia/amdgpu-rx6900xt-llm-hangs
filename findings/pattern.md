# Pattern: hangs happen during prompt reading with MoE experts on the CPU

| Condition | Long-prompt runs | Hangs |
|---|---|---|
| All weights on GPU (`--n-cpu-moe 0`) | dozens: 4K–198K (Qwen3.6-35B-A3B Q2 + vision, 2 builds), up to 247K (Bonsai 27B ternary) | 0 |
| MoE experts partly on CPU, short prompts (≤5K) | several | 0 |
| MoE experts partly on CPU, long prompts (≥56K) | 4 | **3** (the only one that passed was a 67K-token read) |

**Hypothesis (unproven):** with experts on the CPU, the GPU alternates between compute bursts and waits
on host-side expert compute and PCIe transfers. That drives rapid DPM / GFXOFF power-state transitions. Given
the SMU driver/firmware interface mismatch (0x40 vs 0x41), the SMU eventually stops answering a
`TransferTableSmu2Dram` (metrics) request, and the device falls off the bus.

The amdgpu driver periodically requests the metrics table itself (sensors / `gpu_metrics`). A userspace
monitor also polled `rocm-smi` every 30 s on this host. Whether polling frequency matters is untested.
