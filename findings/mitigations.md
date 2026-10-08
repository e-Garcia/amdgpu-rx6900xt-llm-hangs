# Mitigation matrix

Each is tested alone, re-running `repro/` with `--n-cpu-moe 8` at 136K.

| # | Mitigation | How | Status |
|---|---|---|---|
| 1 | Pin clocks (no DPM transitions) | `echo high > /sys/class/drm/cardN/device/power_dpm_force_performance_level` | **failed** (incident 4: hung at 67K; GFXOFF still active) |
| 2 | Disable GFXOFF | boot param `amdgpu.ppfeaturemask=0xffff7fff` (`amdgpu.gfx_off` is not a param on 6.8). Others report `0xfff73fff`. Here: `options amdgpu ppfeaturemask=0xffff7fff` in modprobe.d (keeps overdrive bit `0x4000`) + initramfs rebuild | **failed** (incident 5: delayed it, ~330K offloaded tokens passed, then a silent hang) |
| 3 | Match SMU interface | newer kernel (Ubuntu HWE 6.11+/6.14+) | untested |
| 4 | ASPM off | `pcie_aspm=off amdgpu.aspm=0` | untested |
| 5 | Stop userspace SMU polling during inference | pause `rocm-smi`/metrics pollers | untested |
| 6 | Stop streaming expert weights to the GPU during prompt reads | llama-server `--no-op-offload` | **no hang** (~835K fresh offloaded prompt tokens, 7 reads up to 193K; GFXOFF also off): [no-op-offload.md](no-op-offload.md) |
| — | Already active, did **not** prevent it | `noretry=0`, `runpm=0`, `reset_method=1`, `gpu_recovery=1`, `lockup_timeout=10000`, -40 mV undervolt, `snd_hda_intel power_save=0` | — |

Crash capture to set up before testing: `netconsole` to another host, `kernel.softlockup_panic=1`,
`kernel.hardlockup_panic=1`, `kdump`; `umr` for ring/wave state if the GPU hangs without the host dying.

## Related reports (same error family, other hardware/contexts)
- https://discuss.cachyos.org/t/intermittent-hangs-temporary-freeze-in-plasma-amdgpu-smu-im-not-done-with-your-previous-command/15819
- https://bbs.archlinux.org/viewtopic.php?id=310517
- https://lists.opensuse.org/archives/list/factory@lists.opensuse.org/thread/LDI4LKXWBLNMBGI22LRQL4R6MBMBJIA5/
- https://github.com/ROCm/aiter/issues/3139 (MI325X, "Failed to export SMU metrics table" after a hang during a large prompt read)
