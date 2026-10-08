# Privacy rules for this repo

Allowed: hardware models, firmware/driver/kernel/ROCm/llama.cpp versions, kernel log lines about the GPU,
temperatures/VRAM/clock samples, timing numbers, synthetic test prompts.

Never committed:
- user names, host names, home paths, network names, IP/MAC addresses, serial numbers, UUIDs/boot ids,
  emails, phone numbers, chat/Telegram ids, API keys
- **binary dumps or memory images**: core files, `vmcore`, `devcoredump` data, `/proc/*/mem`, GGUF/model
  files, prompt caches. These can contain fragments of real prompts or other private memory.
  Summarize them in text instead (e.g. the decoded ring/IP names), after review.
- real prompts or chat content. Tests use only the synthetic documents in `repro/`.

Process: raw logs → `tools/redact.sh` → manual read → `tools/pii-check.sh` (also enforced in CI).
