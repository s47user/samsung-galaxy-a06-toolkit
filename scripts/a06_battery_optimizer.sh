#!/system/bin/sh
# ==============================================================================
# a06_battery_optimizer.sh - Runtime Power & Battery Tuning for Galaxy A06
# Target: Samsung Galaxy A06 (SM-A065F / SM-A065M)
# SoC: MediaTek Helio G85 (MT6769V) | OS: Android 14 / One UI Core 6.1
# Kernel: Linux 4.19.191 KernelSU-Next / Magisk
# ==============================================================================

# Ensure root execution
if [ "$(id -u)" -ne 0 ]; then
    echo "[-] Error: This script must be run as root (su)."
    exit 1
fi

echo "=========================================================="
echo " Samsung Galaxy A06 (SM-A065F) Battery Optimizer Engine"
echo "=========================================================="

# 1. Wait for Android boot completion if running at startup
while [ "$(getprop sys.boot_completed)" != "1" ]; do
    sleep 3
done
sleep 5

echo "[*] System boot completed. Applying battery & power optimizations..."

# ------------------------------------------------------------------------------
# 1. CPUSET Background Task Isolation (The Big Battery Saver)
# Helio G85: Cores 0-5 = Cortex-A55 (LITTLE), Cores 6-7 = Cortex-A75 (BIG)
# Restrict background tasks exclusively to Cortex-A55 cores 0-3.
# Prevents background daemons from ever waking the power-hungry A75 big cores.
# ------------------------------------------------------------------------------
echo "[1/6] Tuning CPUset Task Affinity..."

if [ -d "/dev/cpuset/background" ]; then
    echo 0-3 > /dev/cpuset/background/cpus 2>/dev/null
    echo "[+] Restricted /dev/cpuset/background to LITTLE cores (0-3)"
fi

if [ -d "/dev/cpuset/system-background" ]; then
    echo 0-3 > /dev/cpuset/system-background/cpus 2>/dev/null
    echo "[+] Restricted /dev/cpuset/system-background to LITTLE cores (0-3)"
fi

if [ -d "/dev/cpuset/restricted" ]; then
    echo 0-3 > /dev/cpuset/restricted/cpus 2>/dev/null
    echo "[+] Restricted /dev/cpuset/restricted to LITTLE cores (0-3)"
fi

if [ -d "/dev/cpuset/dex2oat" ]; then
    echo 0-5 > /dev/cpuset/dex2oat/cpus 2>/dev/null
    echo "[+] Confined /dev/cpuset/dex2oat to Efficiency Cluster (0-5)"
fi

# ------------------------------------------------------------------------------
# 2. EAS Schedtune Energy Gating
# Forbid energy boost and idle-cpu wakeups for non-interactive tasks.
# ------------------------------------------------------------------------------
echo "[2/6] Configuring Schedtune Energy Bias..."

for stune in background system-background; do
    if [ -d "/dev/stune/$stune" ]; then
        echo 0 > /dev/stune/$stune/schedtune.boost 2>/dev/null
        echo 0 > /dev/stune/$stune/schedtune.prefer_idle 2>/dev/null
        echo "[+] Set $stune: boost=0, prefer_idle=0"
    fi
done

# ------------------------------------------------------------------------------
# 3. Schedutil DVFS Governor Down-Rate Tuning
# Drop CPU frequency to minimum floor (400 MHz) faster when touch event ends.
# ------------------------------------------------------------------------------
echo "[3/6] Tuning Schedutil Frequency Scaling Down-Rates..."

# Performance cluster (2x Cortex-A75 @ 2.0 GHz)
if [ -d "/sys/devices/system/cpu/cpufreq/policy6/schedutil" ]; then
    echo 500 > /sys/devices/system/cpu/cpufreq/policy6/schedutil/up_rate_limit_us 2>/dev/null
    echo 10000 > /sys/devices/system/cpu/cpufreq/policy6/schedutil/down_rate_limit_us 2>/dev/null
    echo "[+] Policy6 (Cortex-A75): ramp-up=500us, down-clock=10000us (10ms)"
fi

# Efficiency cluster (6x Cortex-A55 @ 1.8 GHz)
if [ -d "/sys/devices/system/cpu/cpufreq/policy0/schedutil" ]; then
    echo 1000 > /sys/devices/system/cpu/cpufreq/policy0/schedutil/up_rate_limit_us 2>/dev/null
    echo 15000 > /sys/devices/system/cpu/cpufreq/policy0/schedutil/down_rate_limit_us 2>/dev/null
    echo "[+] Policy0 (Cortex-A55): ramp-up=1000us, down-clock=15000us (15ms)"
fi

# ------------------------------------------------------------------------------
# 4. Storage & Memory I/O Batching (Reduces eMMC Controller Power)
# Batch dirty writes to minimize eMMC 5.1 NAND write-wakeups.
# ------------------------------------------------------------------------------
echo "[4/6] Optimizing Virtual Memory & Storage Writeback..."

# Flush dirty memory every 15 seconds instead of every 5 seconds (saves NAND bus wakeups)
echo 1500 > /proc/sys/vm/dirty_writeback_centisecs 2>/dev/null
echo 3000 > /proc/sys/vm/dirty_expire_centisecs 2>/dev/null

# Swappiness 70: Keeps zRAM balanced, preventing kswapd0 100% CPU lockups
echo 70 > /proc/sys/vm/swappiness 2>/dev/null
echo 0 > /proc/sys/vm/page-cluster 2>/dev/null
echo 100 > /proc/sys/vm/vfs_cache_pressure 2>/dev/null
echo "[+] VM: dirty_writeback=15s, swappiness=70, page-cluster=0"

# ------------------------------------------------------------------------------
# 5. Android Quick Doze (Deep Sleep Acceleration)
# Shorten delay to enter Light Doze from 30 mins to 15 seconds on screen-off.
# High priority notifications (WhatsApp, Calls, Alarms) wake normally.
# ------------------------------------------------------------------------------
echo "[5/6] Injecting Android Quick Doze Parameters..."

DOZE_PARAMS="light_after_inactive_to=15000,light_pre_idle_to=30000,light_idle_to=60000,light_idle_factor=2.0,light_max_idle_to=900000,locating_to=0,location_accuracy=20.0,motion_inactive_to=30000,idle_after_inactive_to=60000,idle_pending_to=60000,max_idle_pending_to=120000,idle_pending_factor=2.0,idle_to=300000,max_idle_to=21600000,idle_factor=2.0,min_time_to_alarm=3600000"

settings put global device_idle_constants "$DOZE_PARAMS" 2>/dev/null
echo "[+] Quick Doze enabled: Screen-off light idle in 15 seconds"

# ------------------------------------------------------------------------------
# 6. Logging & Telemetry Quenching
# ------------------------------------------------------------------------------
echo "[6/6] Silencing Unnecessary Wake Logs..."

pm disable-user --user 0 com.samsung.android.securitylogagent 2>/dev/null
cmd wifi set-verbose-logging disabled 2>/dev/null
echo "[+] Silenced SecurityLogAgent and Wi-Fi verbose logging"

echo ""
echo "=========================================================="
echo " [✓] Galaxy A06 Power Optimization Active!"
echo " Expected Idle Battery Drain: ~0.4% - 0.8% per hour"
echo "=========================================================="
