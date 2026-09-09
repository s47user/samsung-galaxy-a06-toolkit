#!/system/bin/sh
MODDIR="${0%/*}"

# Initialize target config directory
mkdir -p /data/adb/a06_shield

if [ ! -f /data/adb/a06_shield/target.txt ]; then
    cat << 'EOF' > /data/adb/a06_shield/target.txt
# A06 Shield - Protected Packages List
# Target apps and services to protect from bootloader/root detection
com.google.android.gms
com.google.android.gms.unstable
com.android.vending
gr.nikolasspyr.integritycheck
com.flinkapps.safteynet
com.supercell.brawlstars
EOF
    chmod 644 /data/adb/a06_shield/target.txt
fi
