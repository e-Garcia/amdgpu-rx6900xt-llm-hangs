#!/usr/bin/env bash
# serve.sh <ctx> <n_cpu_moe> [extra llama-server args]
# Env: BIN (dir with llama-server), MODEL (.gguf), MMPROJ (.gguf, optional), ROCM_LIBS (optional), PORT (default 18092)
set -u
C=$1 NCM=$2; shift 2
: "${BIN:?set BIN}" "${MODEL:?set MODEL}"; PORT=${PORT:-18092}
MM=(); [ -n "${MMPROJ:-}" ] && MM=(--mmproj "$MMPROJ")
cd "$BIN"
LD_LIBRARY_PATH="$BIN${ROCM_LIBS:+:$ROCM_LIBS}" exec ./llama-server -m "$MODEL" "${MM[@]}" --alias test \
  --host 127.0.0.1 --port "$PORT" -ngl 999 --n-cpu-moe "$NCM" -fa on -ctk q8_0 -ctv q8_0 -c "$C" -np 1 \
  --jinja --threads "$(nproc)" --temp 0.6 --top-p 0.95 --top-k 20 --min-p 0 "$@"
