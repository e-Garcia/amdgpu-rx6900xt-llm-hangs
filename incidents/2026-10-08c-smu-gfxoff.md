# Incident 4: 2026-10-08 15:33, SMU stuck on AllowGfxOff (clocks pinned high)

Mitigation #1 test: clean boot after an AC power cycle, `power_dpm_force_performance_level=high`, then the same config
as incidents 2 and 3 (Qwen3.6-35B-A3B Q2 + mmproj, 200K q8_0 KV, `--n-cpu-moe 8`).
- **5K step:** passed (all recall/vision checks, 50 tok/s).
- **67K step:** hung about 2 minutes into reading the prompt.
- **GPU trace** (5-s samples): sclk held at 2500 MHz and mclk at 1000 MHz throughout, so the pin worked. Power swung
  51 → 118 → 174 W and busy 26 → 94 % between samples (GPU bursts alternating with waits on the CPU-side experts).
  Junction 47–61 °C. At idle, sclk read 0 MHz: GFXOFF still powers the GFX block down with the level pinned.

```
15:33:41 amdgpu: SMU: I'm not done with your previous command: SMN_C2PMSG_66:0x00000028 SMN_C2PMSG_82:0x00000000
15:33:41 amdgpu: Failed to enable gfxoff!
15:33:49 amdgpu: SMU: I'm not done with your previous command: SMN_C2PMSG_66:0x00000028 SMN_C2PMSG_82:0x00000000
15:33:49 amdgpu: Failed to export SMU metrics table!
-> last line 15:33:54; host reset; new boot 15:34:42; GPU absent from lspci
```

**Why it matters:** the first message the SMU never finished is `0x28` = `PPSMC_MSG_AllowGfxOff` (smu_v11_0_7 / sienna_cichlid),
not the metrics-table export (`0x12`) seen in incidents 1 and 3; that one failed only afterwards. With MoE experts on the CPU
the GFX block idles many times per second during prompt reading, so it enters and leaves GFXOFF far more often than in
full-GPU runs. Pinning clocks removes DPM transitions but not GFXOFF, which fits mitigation #1 failing.

- **Result:** mitigation #1 (pin clocks) does **not** prevent the hang.
- **Next:** mitigation #2, GFXOFF off (`ppfeaturemask` bit `0x8000` cleared).
- Logs: [../logs/boot-2026-10-08c-kernel-amdgpu.txt](../logs/boot-2026-10-08c-kernel-amdgpu.txt),
  [../logs/boot-2026-10-08c-last-lines.txt](../logs/boot-2026-10-08c-last-lines.txt),
  [../logs/gpu-trace-pinned-clocks-2026-10-08c.txt](../logs/gpu-trace-pinned-clocks-2026-10-08c.txt)
