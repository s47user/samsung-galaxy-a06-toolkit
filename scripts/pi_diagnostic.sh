#!/system/bin/sh
# =====================================================
# Play Integrity Diagnostic Script for SM-A065F
# Run as root: su -c "sh /sdcard/pi_diagnostic.sh"
# =====================================================

echo "============================================"
echo "  PI DIAGNOSTIC — SM-A065F"
echo "  $(date)"
echo "============================================"
echo ""

echo "=== 1. BOOTLOADER & VERIFIED BOOT STATE ==="
echo "ro.boot.verifiedbootstate  = $(getprop ro.boot.verifiedbootstate)"
echo "ro.boot.flash.locked       = $(getprop ro.boot.flash.locked)"
echo "ro.boot.warranty_bit       = $(getprop ro.boot.warranty_bit)"
echo "ro.boot.vbmeta.device_state= $(getprop ro.boot.vbmeta.device_state)"
echo "sys.oem_unlock_allowed     = $(getprop sys.oem_unlock_allowed)"
echo "ro.is_ever_orange          = $(getprop ro.is_ever_orange)"
echo "ro.boot.em.status          = $(getprop ro.boot.em.status)"
echo "ro.warranty_bit            = $(getprop ro.warranty_bit)"
echo "ro.fmp_level               = $(getprop ro.fmp_level)"
echo ""

echo "=== 2. BUILD FINGERPRINTS (ALL OF THEM) ==="
echo "ro.build.fingerprint       = $(getprop ro.build.fingerprint)"
echo "ro.vendor.build.fingerprint= $(getprop ro.vendor.build.fingerprint)"
echo "ro.bootimage.build.fingerprint = $(getprop ro.bootimage.build.fingerprint)"
echo "ro.system.build.fingerprint= $(getprop ro.system.build.fingerprint)"
echo "ro.odm.build.fingerprint   = $(getprop ro.odm.build.fingerprint)"
echo ""

echo "=== 3. BUILD IDENTITY ==="
echo "ro.build.display.id        = $(getprop ro.build.display.id)"
echo "ro.build.version.incremental= $(getprop ro.build.version.incremental)"
echo "ro.build.version.security_patch = $(getprop ro.build.version.security_patch)"
echo "ro.build.type              = $(getprop ro.build.type)"
echo "ro.build.tags              = $(getprop ro.build.tags)"
echo "ro.product.model           = $(getprop ro.product.model)"
echo "ro.product.brand           = $(getprop ro.product.brand)"
echo "ro.product.device          = $(getprop ro.product.device)"
echo "ro.product.name            = $(getprop ro.product.name)"
echo "ro.product.manufacturer    = $(getprop ro.product.manufacturer)"
echo ""

echo "=== 4. FIRST API LEVEL (Critical!) ==="
echo "ro.product.first_api_level = $(getprop ro.product.first_api_level)"
echo "ro.board.first_api_level   = $(getprop ro.board.first_api_level)"
echo "ro.build.version.sdk       = $(getprop ro.build.version.sdk)"
echo ""

echo "=== 5. SELINUX STATUS ==="
echo "SELinux enforce status:"
getenforce 2>/dev/null || echo "(getenforce not found)"
echo ""

echo "=== 6. INSTALLED MODULES ==="
echo "Modules in /data/adb/modules/:"
ls -1 /data/adb/modules/ 2>/dev/null || echo "(No modules directory)"
echo ""
echo "Module details:"
for mod in /data/adb/modules/*/; do
    modname=$(basename "$mod")
    disabled=""
    [ -f "$mod/disable" ] && disabled=" [DISABLED]"
    [ -f "$mod/remove" ] && disabled=" [PENDING REMOVE]"
    desc=""
    [ -f "$mod/module.prop" ] && desc=$(grep "^description=" "$mod/module.prop" 2>/dev/null | cut -d= -f2-)
    echo "  - $modname$disabled: $desc"
done
echo ""

echo "=== 7. PIF CONFIGURATION FILES ==="
echo "--- pif.json ---"
cat /data/adb/modules/playintegrityfix/pif.json 2>/dev/null || echo "(not found)"
echo ""
echo "--- custom.pif.json ---"
cat /data/adb/modules/playintegrityfix/custom.pif.json 2>/dev/null || echo "(not found)"
echo ""
echo "--- pif.prop ---"
cat /data/adb/modules/playintegrityfix/pif.prop 2>/dev/null || echo "(not found)"
echo ""
echo "--- custom.pif.prop ---"
cat /data/adb/modules/playintegrityfix/custom.pif.prop 2>/dev/null || echo "(not found)"
echo ""

echo "=== 8. APATCH STATUS ==="
echo "APatch version:"
cat /data/adb/ap/version 2>/dev/null || echo "(not found at /data/adb/ap/)"
ls /data/adb/kpatch 2>/dev/null && echo "KernelPatch directory exists"
echo ""

echo "=== 9. ZYGISK STATUS ==="
echo "ReZygisk:"
ls /data/adb/modules/zygisksu/module.prop 2>/dev/null && cat /data/adb/modules/zygisksu/module.prop 2>/dev/null
ls /data/adb/modules/rezygisk/module.prop 2>/dev/null && cat /data/adb/modules/rezygisk/module.prop 2>/dev/null
ls /data/adb/modules/neozygisk/module.prop 2>/dev/null && cat /data/adb/modules/neozygisk/module.prop 2>/dev/null
echo ""

echo "=== 10. ROOT ARTIFACTS (What Google Might See) ==="
echo "su binary:     $(which su 2>/dev/null || echo 'not in PATH')"
echo "/system/xbin/su: $(ls -la /system/xbin/su 2>/dev/null || echo 'not found')"
echo "Magisk app:    $(pm list packages 2>/dev/null | grep -i magisk || echo 'not found')"
echo "APatch app:    $(pm list packages 2>/dev/null | grep -i apatch || echo 'not found')"
echo "KSU app:       $(pm list packages 2>/dev/null | grep -i kernelsu || echo 'not found')"
echo ""

echo "=== 11. GOOGLE PLAY SERVICES INFO ==="
echo "GMS version:"
dumpsys package com.google.android.gms 2>/dev/null | grep "versionName" | head -1
echo ""

echo "============================================"
echo "  DIAGNOSTIC COMPLETE"
echo "  Copy all output above and share it"
echo "============================================"
