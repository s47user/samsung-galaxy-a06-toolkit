#!/system/bin/sh
# ==============================================================================
# service.sh - KernelSU / Magisk Late-Service Power Optimizer for Galaxy A06
# Target: Samsung Galaxy A06 (SM-A065F / SM-A065M)
# ==============================================================================

# Wait for boot completion
while [ "$(getprop sys.boot_completed)" != "1" ]; do
    sleep 3
done
sleep 5

# 1. CPUSET Background Task Isolation to Cortex-A55 LITTLE Cores (0-3)
if [ -d "/dev/cpuset/background" ]; then
    echo 0-3 > /dev/cpuset/background/cpus 2>/dev/null
fi
if [ -d "/dev/cpuset/system-background" ]; then
    echo 0-3 > /dev/cpuset/system-background/cpus 2>/dev/null
fi
if [ -d "/dev/cpuset/restricted" ]; then
    echo 0-3 > /dev/cpuset/restricted/cpus 2>/dev/null
fi
if [ -d "/dev/cpuset/dex2oat" ]; then
    echo 0-5 > /dev/cpuset/dex2oat/cpus 2>/dev/null
fi

# 2. EAS Schedtune Energy Bias
for stune in background system-background; do
    if [ -d "/dev/stune/$stune" ]; then
        echo 0 > /dev/stune/$stune/schedtune.boost 2>/dev/null
        echo 0 > /dev/stune/$stune/schedtune.prefer_idle 2>/dev/null
    fi
done

# 3. Schedutil Frequency Scaling Down-Rates (Helio G85)
# Cortex-A75: drop clock in 10ms
if [ -d "/sys/devices/system/cpu/cpufreq/policy6/schedutil" ]; then
    echo 500 > /sys/devices/system/cpu/cpufreq/policy6/schedutil/up_rate_limit_us 2>/dev/null
    echo 10000 > /sys/devices/system/cpu/cpufreq/policy6/schedutil/down_rate_limit_us 2>/dev/null
fi
# Cortex-A55: drop clock in 15ms
if [ -d "/sys/devices/system/cpu/cpufreq/policy0/schedutil" ]; then
    echo 1000 > /sys/devices/system/cpu/cpufreq/policy0/schedutil/up_rate_limit_us 2>/dev/null
    echo 15000 > /sys/devices/system/cpu/cpufreq/policy0/schedutil/down_rate_limit_us 2>/dev/null
fi

# 4. Memory & Storage I/O Writeback Batching
echo 1500 > /proc/sys/vm/dirty_writeback_centisecs 2>/dev/null
echo 3000 > /proc/sys/vm/dirty_expire_centisecs 2>/dev/null
echo 70 > /proc/sys/vm/swappiness 2>/dev/null
echo 0 > /proc/sys/vm/page-cluster 2>/dev/null
echo 100 > /proc/sys/vm/vfs_cache_pressure 2>/dev/null

# 5. Android Quick Doze (15s Screen-Off Light Sleep)
DOZE_PARAMS="light_after_inactive_to=15000,light_pre_idle_to=30000,light_idle_to=60000,light_idle_factor=2.0,light_max_idle_to=900000,locating_to=0,location_accuracy=20.0,motion_inactive_to=30000,idle_after_inactive_to=60000,idle_pending_to=60000,max_idle_pending_to=120000,idle_pending_factor=2.0,idle_to=300000,max_idle_to=21600000,idle_factor=2.0,min_time_to_alarm=3600000"
settings put global device_idle_constants "$DOZE_PARAMS" 2>/dev/null

# 6. Quench Verbose Wake Logs
pm disable-user --user 0 com.samsung.android.securitylogagent 2>/dev/null
cmd wifi set-verbose-logging disabled 2>/dev/null
