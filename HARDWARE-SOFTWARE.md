# Hardware and software (as of 2026-10-08)

| Component | Value |
|---|---|
| GPU (affected) | AMD Radeon RX 6900 XT, Navi 21 / gfx1030, 16 GB, PCI `09:00.0`, VBIOS `115-D412BS2-100` |
| GPU (unaffected, same host) | NVIDIA RTX 3060 12 GB (CUDA, separate workloads) |
| SMU | `smu driver if version = 0x40`, `smu fw if version = 0x41`, fw `58.89.0` (**driver/firmware interface mismatch**) |
| CPU | AMD Ryzen 7 5800X3D (8C/16T) |
| RAM | 96 GB (94 GiB usable) |
| Board | ASUS ROG STRIX B550-F GAMING WIFI II |
| OS | Ubuntu 24.04.5 LTS |
| Kernel | `6.8.0-138-generic` (6.8.0-139 installed, not booted) |
| linux-firmware | `20240318.git3b128b60.0ubuntu3.1` |
| ROCm (system) | 7.1.0 (`rocm-core 7.1.0.70100`, `hip-runtime-amd 7.1.25424`, `amdgpu-core 7.1.70100`) |
| ROCm (used at runtime) | 7.2 user-space libs via `LD_LIBRARY_PATH` (the system 7.1 hipBLAS fails on gfx1030: `hipMallocAsync` → `CUBLAS_STATUS_ALLOC_FAILED`) |
| llama.cpp | source build of upstream PR #28243 (`6fcaa16f4`), HIP; PrismML fork prebuilt `prism-b10754-2459f68` (`bin-ubuntu-rocm-7.2-x64`) |

## Kernel command line (GPU-related)
`amdgpu.noretry=0 amdgpu.runpm=0 amd_iommu=on iommu=pt pcie_acs_override=downstream,multifunction`

## `/etc/modprobe.d/amdgpu.conf`
```
options amdgpu noretry=0 reset_method=1 ras_enable=1 gpu_recovery=1 runpm=0 lockup_timeout=10000,10000,10000,10000
```
Also: `snd_hda_intel power_save=0` (HDMI-audio PM fix), and a **-40 mV `OD_VDDGFX_OFFSET` undervolt** applied at boot.
GPU temperature at every hang: 53–65 °C. VRAM 13–14 of 16 GB.

## Models and server flags at the hangs
- #1: Qwen3.8-Flash-Next 125B-A6B UD-IQ3_XXS, `-ngl 99 --n-cpu-moe 46 -c 204800 -ctk q8_0 -ctv q8_0 --spec-type draft-mtp`, 16 threads
- #2/#3: Qwen3.6-35B-A3B UD-Q2_K_XL + `mmproj-F16`, `-ngl 999 --n-cpu-moe 8 -fa on -ctk q8_0 -ctv q8_0 -c 204800 -np 1 --jinja --threads 16`
