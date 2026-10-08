# Incident 1: 2026-09-30 07:17, SMU failure during Flash-Next prompt reading

- **Workload:** llama.cpp (PR #28243 build), Qwen3.8-Flash-Next 125B-A6B with `--n-cpu-moe 46`, reading a long prompt at
  ~195–200 tok/s. Progress was logged normally up to 56,244 tokens.
- **Monitoring until 07:16:58:** 13/15 GB VRAM, 54 °C. Normal.
- **07:17:00–07:17:01:** six of `SMU: response:0xFFFFFFFF for index:18 param:0x00000005 message:TransferTableSmu2Dram?`
  and `Failed to export SMU metrics table!`.
- **07:17:16 / 07:17:26:** `workqueue: vmstat_update hogged CPU`, `wait_rcu_exp_gp hogged CPU`.
- **~45 s of silence**, then a new boot with **no clean shutdown sequence**.
- **New boot:** no amdgpu probe at all. The card was absent from `lspci` until an AC power cycle.
- Index 18 / message 0x12 = `TransferTableSmu2Dram`, the same as incident 3.
