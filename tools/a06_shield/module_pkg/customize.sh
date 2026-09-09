SKIPUNZIP=0

ui_print "****************************************"
ui_print "       A06 Integrity Shield v1.0        "
ui_print "    Specialized for Samsung SM-A065F    "
ui_print "****************************************"

# Verify architecture
if [ "$ARCH" != "arm64" ]; then
    abort "! Unsupported architecture: $ARCH (Requires arm64)"
fi

ui_print "- Installing native Zygisk hooks..."
set_perm_recursive $MODPATH 0 0 0755 0644
set_perm $MODPATH/zygisk/arm64-v8a.so 0 0 0755
set_perm $MODPATH/post-fs-data.sh 0 0 0755
set_perm $MODPATH/service.sh 0 0 0755

ui_print "- Creating default target configuration..."
mkdir -p /data/adb/a06_shield
if [ ! -f /data/adb/a06_shield/target.txt ]; then
    cat << 'EOF' > /data/adb/a06_shield/target.txt
com.google.android.gms
com.google.android.gms.unstable
com.android.vending
gr.nikolasspyr.integritycheck
com.flinkapps.safteynet
com.supercell.brawlstars
EOF
    chmod 644 /data/adb/a06_shield/target.txt
fi

ui_print " "
ui_print "- Installation complete! Please reboot."
