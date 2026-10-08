# Incident 3: 2026-10-08 12:13, SMU failure, card drops off the bus (clean-boot repro of #2)

Same config as incident 2, on a fresh boot with no prior GPU faults.
- **5K step:** passed (47 tok/s).
- **67K step:** passed (prompt read at 996 tok/s, 27.5 tok/s generation).
- **136K step:** prompt reading progressed normally (~900 tok/s) to ~90K tokens, then:
```
12:13:48 amdgpu 0000:09:00.0: amdgpu: SMU: I'm not done with your previous command: SMN_C2PMSG_66:0x00000012 SMN_C2PMSG_82:0x00000005
12:13:48 amdgpu 0000:09:00.0: amdgpu: Failed to export SMU metrics table!
12:13:57 (repeated) -> last line; host reset; new boot 12:14:40; GPU absent from lspci, amdgpu not loaded
```
- **GPU state:** 63–64 °C, 14/15 GB VRAM.
- **Recovery:** needs an AC power cycle.
- Logs: [../logs/boot-2026-10-08b-kernel-amdgpu.txt](../logs/boot-2026-10-08b-kernel-amdgpu.txt),
  [../logs/boot-2026-10-08b-last-lines.txt](../logs/boot-2026-10-08b-last-lines.txt),
  [../logs/llama-server-prefill-before-hang2.txt](../logs/llama-server-prefill-before-hang2.txt)
