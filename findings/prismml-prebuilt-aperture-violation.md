# Separate bug: PrismML llama.cpp prebuilt b10754 GPU-faults on image + `--n-cpu-moe`

Binary: `llama-prism-b10754-2459f68` (`bin-ubuntu-rocm-7.2-x64`), gfx1030, ROCm 7.2 libs.
Model: Qwen3.6-35B-A3B UD-Q2_K_XL + `mmproj-F16`.

| Config | Result |
|---|---|
| text-only request, `--n-cpu-moe 8` | OK (~49 tok/s) |
| image request, `--n-cpu-moe 0` | OK |
| image request, `--n-cpu-moe` ≥ 1 | **aborts on first request** |
| + `HSA_XNACK=1`, + `--no-host`, + `--no-mmproj-offload` | still aborts |
| same request on llama.cpp PR #28243 source build | OK |

```
HSA_STATUS_ERROR_MEMORY_APERTURE_VIOLATION: The agent attempted to access memory beyond the largest legal address. code: 0x29
ROCm error: an illegal memory access was encountered
  in function ggml_backend_cuda_synchronize ... hipStreamSynchronize(cuda_ctx->stream())
```
Also seen when VRAM was nearly full: `CUBLAS_STATUS_ALLOC_FAILED` on the first request (hipBLAS workspace).
Next step: capture with the ROCm debug agent (`HSA_TOOLS_LIB=librocm-debug-agent.so.2`) and report upstream.
