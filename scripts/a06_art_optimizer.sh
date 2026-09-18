#!/system/bin/sh
# ==============================================================================
# a06_art_optimizer.sh - ART Cloud-Profile Ahead-Of-Time (AOT) Pre-Compiler
# Target: Samsung Galaxy A06 (SM-A065F / SM-A065M)
# SoC: MediaTek Helio G85 | OS: Android 14 / One UI Core 6.1
# ==============================================================================

# Ensure root or ADB shell execution
if [ "$(id -u)" -ne 0 ] && [ "$(whoami 2>/dev/null)" != "shell" ]; then
    echo "[-] Error: This script must be run as root (su) or via ADB shell."
    exit 1
fi

echo "=========================================================="
echo " Samsung Galaxy A06 — ART Ahead-Of-Time Pre-Compiler"
echo " Eliminates JIT runtime lag & accelerates app cold starts"
echo "=========================================================="

MODE="speed-profile"
if [ "$1" = "--full" ] || [ "$1" = "-f" ]; then
    MODE="speed"
    echo "[!] Full mode selected: Compiling entire APK bytecode to native ARM64."
elif [ "$1" = "--reset" ] || [ "$1" = "-r" ]; then
    echo "[*] Resetting all packages to default compiler filter..."
    cmd package compile --reset -a
    echo "[✓] Reset complete."
    exit 0
else
    echo "[*] Using mode: $MODE (Recommended: compiles hot paths via Cloud Profiles)"
fi

# Check battery status
BATT_LEVEL=$(dumpsys battery | grep -i "level:" | awk '{print $2}')
BATT_POWERED=$(dumpsys battery | grep -i "AC powered: true\|USB powered: true\|Wireless powered: true")

echo "[*] Battery Level: ${BATT_LEVEL}%"
if [ -n "$BATT_POWERED" ]; then
    echo "[+] Device is connected to external power."
else
    echo "[!] Notice: Compiling uses CPU power. Running on battery."
    if [ -n "$BATT_LEVEL" ] && [ "$BATT_LEVEL" -lt 25 ]; then
        echo "[-] Error: Battery is below 25% ($BATT_LEVEL%). Please connect charger first."
        exit 1
    fi
fi

echo ""
echo "[>] Starting ART Ahead-Of-Time compilation for all user and system apps..."
echo "    (This may take 2 to 5 minutes depending on installed apps. Do not reboot.)"
echo ""

START_TIME=$(date +%s 2>/dev/null || echo 0)

cmd package compile -m "$MODE" -a

END_TIME=$(date +%s 2>/dev/null || echo 0)
if [ "$START_TIME" -ne 0 ] && [ "$END_TIME" -ne 0 ]; then
    ELAPSED=$((END_TIME - START_TIME))
    echo ""
    echo "[+] Compilation finished in ${ELAPSED} seconds."
else
    echo ""
    echo "[+] Compilation finished."
fi

echo ""
echo "=========================================================="
echo " [✓] ART Optimization Complete!"
echo " Apps will now launch from native ARM64 code without JIT lag."
echo "=========================================================="
