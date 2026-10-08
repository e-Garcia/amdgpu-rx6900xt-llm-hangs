#!/usr/bin/env bash
# collect-env.sh : print versions/config relevant to this issue, passed through tools/redact.sh.
cd "$(dirname "$0")/.."
{
echo "## kernel"; uname -r; cat /proc/cmdline
echo "## os"; (lsb_release -ds || cat /etc/os-release) 2>/dev/null
echo "## gpu"; lspci -nn | grep -iE 'vga|display|3d'
echo "## amdgpu boot lines"; (journalctl -b -k --no-pager 2>/dev/null || dmesg) | grep -iE 'smu driver if version|ATOM BIOS|SMU is initialized|amdgpu: .*version' | sed -E 's/^.*kernel: //'
echo "## amdgpu params"; for p in noretry runpm reset_method gpu_recovery lockup_timeout ppfeaturemask aspm; do printf '%s=' $p; cat /sys/module/amdgpu/parameters/$p 2>/dev/null || echo '?'; done
echo "## packages"; dpkg -l 2>/dev/null | awk '/^ii/ && ($2 ~ /^(linux-firmware|rocm-core|hip-runtime-amd|amdgpu-core|amdgpu-dkms|mesa-vulkan-drivers)$/){print $2, $3}'
echo "## power"; for d in /sys/class/drm/card*/device; do [ "$(cat $d/vendor 2>/dev/null)" = 0x1002 ] && { cat $d/power_dpm_force_performance_level; grep -A1 OD_VDDGFX_OFFSET $d/pp_od_clk_voltage 2>/dev/null; }; done
echo "## cpu/ram"; grep -m1 'model name' /proc/cpuinfo; free -g | awk '/Mem/{print $2" GiB"}'
} 2>&1 | tools/redact.sh
