#!/system/bin/sh
SKIPUNZIP=0

ui_print "************************************************"
ui_print "     Samsung Galaxy A06 (SM-A065F)             "
ui_print "       One UI Full Experience Suite             "
ui_print "************************************************"
ui_print " Author: s47user                                "
ui_print " Target: Android 14 / One UI Core 6.1           "
ui_print " Mechanism: Systemless CSC & Floating Feature   "
ui_print "************************************************"

MODEL=$(getprop ro.product.model)
DEVICE=$(getprop ro.product.device)
CSC=$(getprop ro.csc.sales_code)
[ -z "$CSC" ] && CSC=$(getprop persist.omc.sales_code)
[ -z "$CSC" ] && CSC=$(getprop ril.official_csc)

ui_print "- Device: $MODEL ($DEVICE)"
ui_print "- Active Sales Code (CSC): ${CSC:-Unknown}"

ui_print "- Features being enabled:"
ui_print "  [✓] Real-Time Network Speed Indicator (Status Bar)"
ui_print "  [✓] Native 2-Way Hardware Call Recording"
ui_print "  [✓] Camera Shutter Sound Toggle (Settings Menu)"
ui_print "  [✓] Full 1080p Screen Recorder + PIP + QS Tile"
ui_print "  [✓] System-Wide Dolby Atmos & Stereo SoundAlive"
ui_print "  [✓] Smart Call / Spam Protection"
ui_print "  [✓] Separate App Sound (MultiSound)"
ui_print "  [✓] High-End Launcher Animations & Blur"

ui_print "- Setting executable permissions..."
set_perm $MODPATH/bin/sec-omc-coder 0 0 0755
set_perm $MODPATH/post-fs-data.sh 0 0 0755
set_perm $MODPATH/service.sh 0 0 0755
if [ -f "$MODPATH/system/etc/floating_feature.xml" ]; then
    set_perm $MODPATH/system/etc/floating_feature.xml 0 0 0644
fi

mkdir -p $MODPATH/cache
set_perm $MODPATH/cache 0 0 0755

ui_print "************************************************"
ui_print " Installation Succeeded!                        "
ui_print " Please reboot your device to activate features."
ui_print "************************************************"
