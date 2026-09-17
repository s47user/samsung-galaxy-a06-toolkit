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

exit 0
