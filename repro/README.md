# Reproduce

**A successful reproduction hangs the host and needs an AC power cycle.** Save your work. Set up crash
capture first (see `../findings/mitigations.md`).

1. `repro/collect-env.sh > env.txt` and attach it to issues.
2. Start the server: Qwen3.6-35B-A3B UD-Q2_K_XL + `mmproj-F16` from `unsloth/Qwen3.6-35B-A3B-GGUF`.
   ```
   BIN=/path/to/llama.cpp/build-hip/bin MODEL=Qwen3.6-35B-A3B-UD-Q2_K_XL.gguf MMPROJ=mmproj-F16.gguf \
     ROCM_LIBS=/path/to/rocm-7.2/lib repro/serve.sh 204800 8
   ```
3. In another shell, send synthetic long prompts (one image plus a generated ops log, no real data):
   ```
   python3 repro/longprompt_test.py run1 http://127.0.0.1:18092/v1 test 4000 64000 130000
   ```
   It writes `repro/results/*.jsonl` (gitignored). It needs `pip install pillow`.
4. **Control:** the same with `repro/serve.sh 204800 0` (no CPU offload). It has never hung on our host.
5. **Workaround check:** `repro/serve.sh 204800 8 --no-op-offload`. No hang so far on our host (see `../findings/no-op-offload.md`).

The test checks recall, corrected facts, distractors, hallucination and vision at each size, and prints
prompt-read and generation speed.
