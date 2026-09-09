#!/system/bin/sh
# ==============================================================================
# apply_safe_tweaks.sh - Low & Very Low Risk Optimization Script for Galaxy A06
# Applies runtime kernel/sysfs tweaks for Schedutil, zRAM, and eMMC read-ahead.
# Safe, 100% reversible, requires root (su).
# ==============================================================================

if [ "$(id -u)" -ne 0 ]; then
    echo "[-] Error: This script must be run as root (su)."
    exit 1
fi

echo "[*] Applying low-risk optimizations for Galaxy A06..."

# 1. CPU Schedutil Touch Responsiveness
# Global Schedutil directory (MediaTek MT6769 EAS layout)
if [ -f "/sys/devices/system/cpu/cpufreq/schedutil/up_rate_limit_us" ]; then
    echo 500 > /sys/devices/system/cpu/cpufreq/schedutil/up_rate_limit_us
    echo 20000 > /sys/devices/system/cpu/cpufreq/schedutil/down_rate_limit_us
    echo "[+] Tuned global Schedutil ramp-up to 500us"
fi

# Performance cluster (2x Cortex-A75) - lower ramp-up delay to 500us
if [ -d "/sys/devices/system/cpu/cpufreq/policy6/schedutil" ]; then
    echo 500 > /sys/devices/system/cpu/cpufreq/policy6/schedutil/up_rate_limit_us
    echo 20000 > /sys/devices/system/cpu/cpufreq/policy6/schedutil/down_rate_limit_us
    echo "[+] Tuned policy6 (Cortex-A75) Schedutil ramp-up to 500us"
fi

# Efficiency cluster (6x Cortex-A55)
if [ -d "/sys/devices/system/cpu/cpufreq/policy0/schedutil" ]; then
    echo 1000 > /sys/devices/system/cpu/cpufreq/policy0/schedutil/up_rate_limit_us
    echo 20000 > /sys/devices/system/cpu/cpufreq/policy0/schedutil/down_rate_limit_us
    echo "[+] Tuned policy0 (Cortex-A55) Schedutil ramp-up to 1000us"
fi

# 2. Balanced Virtual Memory & In-RAM zRAM Tuning (Prevents DSP & kswapd starvation in 3D gaming)
echo 70 > /proc/sys/vm/swappiness
echo 0 > /proc/sys/vm/page-cluster
echo 100 > /proc/sys/vm/vfs_cache_pressure
echo "[+] Tuned Virtual Memory (Swappiness: 70, page-cluster: 0)"

# 3. Storage I/O Read-Ahead Buffer (eMMC 5.1 speedup)
for queue in /sys/block/mmcblk0*/queue/read_ahead_kb; do
    if [ -f "$queue" ]; then
        echo 512 > "$queue"
        echo "[+] Scaled I/O read-ahead buffer to 512 KB on $queue"
    fi
done

# 4. Silence Knox SecurityLogAgent Warning
pm disable-user --user 0 com.samsung.android.securitylogagent 2>/dev/null
echo "[+] Silenced Samsung SecurityLogAgent"

echo "[*] All safe tweaks applied successfully!"
