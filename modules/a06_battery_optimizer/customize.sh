SKIPUNZIP=0

ui_print "***************************************************"
ui_print "  Samsung Galaxy A06 Power Optimizer Engine        "
ui_print "  Helio G85 (MT6769V) | Android 14 / One UI 6.1    "
ui_print "***************************************************"

set_perm $MODPATH/service.sh 0 0 0755
ui_print "[✓] Schedutil & CPUset power optimizations configured!"
