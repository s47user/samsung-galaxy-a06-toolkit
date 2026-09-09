#!/system/bin/sh
MODDIR="${0%/*}"

# Wait until boot completes
until [ "$(getprop sys.boot_completed)" = "1" ]; do
    sleep 1
done

# Ensure permissions on config
chmod -R 755 /data/adb/a06_shield 2>/dev/null
