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

# 4. Sector 1: eMMC 5.1 Storage & I/O Optimization
for queue in /sys/block/mmcblk*/queue; do
    if [ -d "$queue" ]; then
        [ -f "$queue/scheduler" ] && echo "mq-deadline" > "$queue/scheduler" 2>/dev/null
        [ -f "$queue/read_ahead_kb" ] && echo "128" > "$queue/read_ahead_kb" 2>/dev/null
        [ -f "$queue/add_random" ] && echo "0" > "$queue/add_random" 2>/dev/null
        [ -f "$queue/rq_affinity" ] && echo "2" > "$queue/rq_affinity" 2>/dev/null
        [ -f "$queue/iostats" ] && echo "0" > "$queue/iostats" 2>/dev/null
    fi
done

# 5. Sector 2: Pure in-RAM zRAM VM Tuning
echo "100" > /proc/sys/vm/swappiness 2>/dev/null
echo "70" > /proc/sys/vm/vfs_cache_pressure 2>/dev/null
echo "15" > /proc/sys/vm/dirty_ratio 2>/dev/null
echo "5" > /proc/sys/vm/dirty_background_ratio 2>/dev/null
echo "0" > /proc/sys/vm/page-cluster 2>/dev/null

# 6. Sector 3: Schedutil Governor Curve (0.5ms touch burst / 20ms hold)
for gov in /sys/devices/system/cpu/cpufreq/schedutil /sys/devices/system/cpu/cpu*/cpufreq/schedutil; do
    if [ -d "$gov" ]; then
        [ -f "$gov/up_rate_limit_us" ] && echo "500" > "$gov/up_rate_limit_us" 2>/dev/null
        [ -f "$gov/down_rate_limit_us" ] && echo "20000" > "$gov/down_rate_limit_us" 2>/dev/null
    fi
done

# 7. Sector 4: Safe, balanced Doze profile
cmd deviceidle step 2>/dev/null

exit 0
