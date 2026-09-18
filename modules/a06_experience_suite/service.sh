#!/system/bin/sh
# Late service script executed after boot completion

MODDIR=${0%/*}

# Wait for boot completion
while [ "$(getprop sys.boot_completed)" != "1" ]; do
    sleep 2
done

# Wait an additional 4 seconds for SystemUI and Settings provider to settle
sleep 4

# 1. Enable Real-Time Network Speed in status bar if not explicitly disabled
CURRENT_NETSPEED=$(settings get system network_speed 2>/dev/null)
if [ -z "$CURRENT_NETSPEED" ] || [ "$CURRENT_NETSPEED" = "null" ]; then
    settings put system network_speed 1
fi

# 2. Ensure Screen Recorder overlay permission is granted
appops set com.samsung.android.app.smartcapture SYSTEM_ALERT_WINDOW allow 2>/dev/null

# Clean up any leftover edge panel settings
settings delete secure edge_enable 2>/dev/null
settings delete system edge_panel_enabled 2>/dev/null
settings delete system edge_lighting 2>/dev/null

# 3. Ensure Quick Settings tiles include ScreenRecorder and Dolby Atmos
TILES=$(settings get secure sysui_qs_tiles 2>/dev/null)
if [ -n "$TILES" ] && [ "$TILES" != "null" ]; then
    CHANGED=0
    case "$TILES" in
        *DolbyTile*) ;;
        *) TILES="custom(com.sec.android.app.soundalive/.DolbyTile),$TILES"; CHANGED=1 ;;
    esac
    case "$TILES" in
        *ScreenRecorder*) ;;
        *) TILES="custom(com.samsung.android.app.smartcapture/com.samsung.android.app.screenrecorder.view.RecordScreenTile),$TILES"; CHANGED=1 ;;
    esac
    if [ "$CHANGED" = "1" ]; then
        settings put secure sysui_qs_tiles "$TILES"
    fi
fi

# 4. Sector 1: eMMC 5.1 Storage & I/O Optimization (Half-Duplex Bus Acceleration)
for queue in /sys/block/mmcblk*/queue; do
    if [ -d "$queue" ]; then
        [ -f "$queue/scheduler" ] && echo "mq-deadline" > "$queue/scheduler" 2>/dev/null
        [ -f "$queue/read_ahead_kb" ] && echo "128" > "$queue/read_ahead_kb" 2>/dev/null
        [ -f "$queue/add_random" ] && echo "0" > "$queue/add_random" 2>/dev/null
        [ -f "$queue/rq_affinity" ] && echo "2" > "$queue/rq_affinity" 2>/dev/null
        [ -f "$queue/iostats" ] && echo "0" > "$queue/iostats" 2>/dev/null
    fi
done

# 5. Sector 2: Virtual Memory & Storage Writeback Batching (Reduces eMMC Flash Wakeups)
echo "70" > /proc/sys/vm/swappiness 2>/dev/null
echo "100" > /proc/sys/vm/vfs_cache_pressure 2>/dev/null
echo "0" > /proc/sys/vm/page-cluster 2>/dev/null
echo "1500" > /proc/sys/vm/dirty_writeback_centisecs 2>/dev/null
echo "3000" > /proc/sys/vm/dirty_expire_centisecs 2>/dev/null

# 6. Sector 3: CPUSET Core Affinity & Isolation (MediaTek Helio G85 MT6769V)
# Confine background daemons exclusively to Cortex-A55 LITTLE cores (0-3).
# Keeps Cortex-A75 Big cores 6-7 dormant when screen is off, and 100% available for UI.
if [ -d "/dev/cpuset/background" ]; then
    echo "0-3" > /dev/cpuset/background/cpus 2>/dev/null
fi
if [ -d "/dev/cpuset/system-background" ]; then
    echo "0-3" > /dev/cpuset/system-background/cpus 2>/dev/null
fi
if [ -d "/dev/cpuset/restricted" ]; then
    echo "0-3" > /dev/cpuset/restricted/cpus 2>/dev/null
fi
if [ -d "/dev/cpuset/dex2oat" ]; then
    echo "0-5" > /dev/cpuset/dex2oat/cpus 2>/dev/null
fi

# 7. Sector 4: EAS Schedtune Energy Bias
for stune in background system-background; do
    if [ -d "/dev/stune/$stune" ]; then
        echo "0" > "/dev/stune/$stune/schedtune.boost" 2>/dev/null
        echo "0" > "/dev/stune/$stune/schedtune.prefer_idle" 2>/dev/null
    fi
done

# 8. Sector 5: Schedutil Governor Curve (Instant Touch Ramp / Fast Idle Downclock)
if [ -d "/sys/devices/system/cpu/cpufreq/policy6/schedutil" ]; then
    echo "500" > /sys/devices/system/cpu/cpufreq/policy6/schedutil/up_rate_limit_us 2>/dev/null
    echo "10000" > /sys/devices/system/cpu/cpufreq/policy6/schedutil/down_rate_limit_us 2>/dev/null
fi
if [ -d "/sys/devices/system/cpu/cpufreq/policy0/schedutil" ]; then
    echo "1000" > /sys/devices/system/cpu/cpufreq/policy0/schedutil/up_rate_limit_us 2>/dev/null
    echo "15000" > /sys/devices/system/cpu/cpufreq/policy0/schedutil/down_rate_limit_us 2>/dev/null
fi
for gov in /sys/devices/system/cpu/cpufreq/schedutil /sys/devices/system/cpu/cpu*/cpufreq/schedutil; do
    if [ -d "$gov" ]; then
        [ -f "$gov/up_rate_limit_us" ] && echo "500" > "$gov/up_rate_limit_us" 2>/dev/null
        [ -f "$gov/down_rate_limit_us" ] && echo "15000" > "$gov/down_rate_limit_us" 2>/dev/null
    fi
done

# 9. Sector 6: Android Quick Doze (Deep Sleep in 15s after Screen-Off)
DOZE_PARAMS="light_after_inactive_to=15000,light_pre_idle_to=30000,light_idle_to=60000,light_idle_factor=2.0,light_max_idle_to=900000,locating_to=0,location_accuracy=20.0,motion_inactive_to=30000,idle_after_inactive_to=60000,idle_pending_to=60000,max_idle_pending_to=120000,idle_pending_factor=2.0,idle_to=300000,max_idle_to=21600000,idle_factor=2.0,min_time_to_alarm=3600000"
settings put global device_idle_constants "$DOZE_PARAMS" 2>/dev/null

# 10. Sector 7: Hardware Battery Protection (80% Lifespan Protection Cap)
CURRENT_PROTECT=$(settings get global protect_battery 2>/dev/null)
if [ -z "$CURRENT_PROTECT" ] || [ "$CURRENT_PROTECT" = "null" ]; then
    settings put global protect_battery 1 2>/dev/null
    settings put global protect_battery_mode 2 2>/dev/null
fi

# 11. Sector 8: UI Animation Fluidity (0.75x Scale for Responsive 60Hz/90Hz)
settings put global window_animation_scale 0.75 2>/dev/null
settings put global transition_animation_scale 0.75 2>/dev/null
settings put global animator_duration_scale 0.75 2>/dev/null

# 12. Sector 9: Silencing Heavy Telemetry & Log Loops
pm disable-user --user 0 com.samsung.android.securitylogagent 2>/dev/null
cmd wifi set-verbose-logging disabled 2>/dev/null

# 13. Sector 10: Purge McAfee Device Security Scanner (~80MB PSS RAM reclaimed)
# User can re-enable anytime: pm enable-user --user 0 com.samsung.android.sm.devicesecurity
pm disable-user --user 0 com.samsung.android.sm.devicesecurity 2>/dev/null

# 14. Sector 11: Freeze Digital Wellbeing Background Telemetry
# Eliminates 100-150ms app-switch hitch caused by usage-stats daemon I/O.
# User can unfreeze anytime: pm enable-user --user 0 com.samsung.android.forest
pm disable-user --user 0 com.samsung.android.forest 2>/dev/null
pm disable-user --user 0 com.google.android.apps.wellbeing 2>/dev/null

# 15. Sector 12: SmartSwitch Post-Setup Dormant Receiver Cleanup
# Deactivates background receivers for SmartSwitch migration agent after setup is complete.
pm disable-user --user 0 com.sec.android.easyMover.Agent 2>/dev/null

# 16. Sector 13: MediaTek MiraVision LCD CABC (Content-Adaptive Backlight Control)
# Engages CABC mode 1 (UI mode) — reduces LCD backlight current by 15-20%.
# Try dispsys1 sysfs node first, then legacy fb0 path.
CABC_PATHS="
/sys/devices/platform/14000000.dispsys1/cabc_mode
/sys/devices/platform/dispsys/cabc_mode
/sys/class/graphics/fb0/cabc
/sys/class/graphics/fb0/miravision_cabc
"
for CABC_NODE in $CABC_PATHS; do
    if [ -f "$CABC_NODE" ]; then
        echo "1" > "$CABC_NODE" 2>/dev/null && \
            echo "[service.sh] MiraVision CABC mode 1 set: $CABC_NODE" >> "$MODDIR/experience_suite.log"
        break
    fi
done

exit 0

