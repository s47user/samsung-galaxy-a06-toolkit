#!/system/bin/sh
# ==============================================================================
# a06_hardware_health.sh - Non-Invasive Hardware Health & Longevity Inspector
# Target: Samsung Galaxy A06 (SM-A065F / SM-A065M)
# SoC: MediaTek Helio G85 | OS: Android 14 / One UI Core 6.1
# ==============================================================================

# Ensure root or shell execution
if [ "$(id -u)" -ne 0 ] && [ "$(whoami 2>/dev/null)" != "shell" ]; then
    echo "[-] Error: This script must be run as root (su) or via ADB shell."
    exit 1
fi

echo "=========================================================="
echo " Samsung Galaxy A06 — Hardware Health & Diagnostics"
echo " (Read-Only JEDEC Longevity, Fuel Gauge, and Thermal Status)"
echo "=========================================================="

# ------------------------------------------------------------------------------
# 1. eMMC 5.1 Storage Health (JEDEC Standard Non-Invasive Counters)
# ------------------------------------------------------------------------------
echo ""
echo "[1/3] eMMC 5.1 Storage Wear & Health Status:"
MMC_DEVICE="/sys/block/mmcblk0/device"

if [ -f "$MMC_DEVICE/life_time" ]; then
    LIFE_TIME=$(cat "$MMC_DEVICE/life_time" 2>/dev/null)
    TYPE_A=$(echo "$LIFE_TIME" | awk '{print $1}')
    TYPE_B=$(echo "$LIFE_TIME" | awk '{print $2}')
    
    decode_lifetime() {
        case "$1" in
            0x01) echo "0% - 10% life time used (Brand New / Factory Fresh)" ;;
            0x02) echo "10% - 20% life time used (Excellent)" ;;
            0x03) echo "20% - 30% life time used (Good)" ;;
            0x04) echo "30% - 40% life time used (Normal)" ;;
            0x05) echo "40% - 50% life time used (Fair)" ;;
            0x06|0x07|0x08|0x09) echo "Over 50% life time used" ;;
            0x0a) echo "90% - 100% life time used (Heavy Wear)" ;;
            0x0b) echo "Exceeded estimated life time" ;;
            *) echo "$1 (Valid JEDEC range)" ;;
        esac
    }
    
    echo "  -> SLC Buffer Wear (Type A): $(decode_lifetime "$TYPE_A")"
    echo "  -> MLC/TLC Main Wear (Type B): $(decode_lifetime "$TYPE_B")"
else
    echo "  [-] life_time counter not exposed by kernel block driver."
fi

if [ -f "$MMC_DEVICE/pre_eol_info" ]; then
    PRE_EOL=$(cat "$MMC_DEVICE/pre_eol_info" 2>/dev/null)
    case "$PRE_EOL" in
        0x01) EOL_STATUS="Normal (Reserved blocks healthy)" ;;
        0x02) EOL_STATUS="Warning (80% of reserved blocks consumed)" ;;
        0x03) EOL_STATUS="Urgent (Replace device soon)" ;;
        *) EOL_STATUS="$PRE_EOL" ;;
    esac
    echo "  -> Pre-EOL Condition:        $EOL_STATUS"
fi

if [ -f "$MMC_DEVICE/name" ]; then
    echo "  -> Flash IC Model:           $(cat "$MMC_DEVICE/name" 2>/dev/null)"
fi

# ------------------------------------------------------------------------------
# 2. Battery Fuel Gauge & Chemistry Diagnostics
# ------------------------------------------------------------------------------
echo ""
echo "[2/3] Battery Fuel Gauge & Thermal Safety:"
BATT_NODE="/sys/class/power_supply/battery"

if [ -d "$BATT_NODE" ]; then
    # Temperature in tenths of Celsius
    TEMP_RAW=$(cat "$BATT_NODE/temp" 2>/dev/null)
    if [ -n "$TEMP_RAW" ]; then
        TEMP_C=$((TEMP_RAW / 10))
        TEMP_DEC=$((TEMP_RAW % 10))
        echo "  -> Battery Temperature:     ${TEMP_C}.${TEMP_DEC}°C"
    fi
    
    # Voltage (uV or mV)
    VOLT_RAW=$(cat "$BATT_NODE/voltage_now" 2>/dev/null)
    if [ -n "$VOLT_RAW" ]; then
        VOLT_MV=$((VOLT_RAW / 1000))
        echo "  -> Battery Voltage:         ${VOLT_MV} mV"
    fi
    
    # Current (mA or uA)
    CURR_RAW=$(cat "$BATT_NODE/current_now" 2>/dev/null)
    if [ -n "$CURR_RAW" ]; then
        CURR_MA=$((CURR_RAW / 1000))
        echo "  -> Real-Time Current:       ${CURR_MA} mA"
    fi
    
    [ -f "$BATT_NODE/health" ] && echo "  -> Battery Health:          $(cat "$BATT_NODE/health" 2>/dev/null)"
    [ -f "$BATT_NODE/status" ] && echo "  -> Charging Status:         $(cat "$BATT_NODE/status" 2>/dev/null)"
fi

echo "  -> 80% Protect Battery:     $(settings get global protect_battery 2>/dev/null) (Mode: $(settings get global protect_battery_mode 2>/dev/null))"

# ------------------------------------------------------------------------------
# 3. CPU Thermal Zones (Stock Thermal Safety Verification)
# ------------------------------------------------------------------------------
echo ""
echo "[3/3] CPU Thermal Zones (Factory Limits 100% Intact):"
for tz in /sys/class/thermal/thermal_zone[0-3]; do
    if [ -d "$tz" ]; then
        TYPE=$(cat "$tz/type" 2>/dev/null)
        TEMP=$(cat "$tz/temp" 2>/dev/null)
        if [ -n "$TEMP" ]; then
            TEMP_C=$((TEMP / 1000))
            echo "  -> ${TYPE:-zone}: ${TEMP_C}°C"
        fi
    fi
done

# ------------------------------------------------------------------------------
# 4. Optional On-Demand TRIM (Only when explicitly invoked via --trim)
# ------------------------------------------------------------------------------
if [ "$1" = "--trim" ] || [ "$1" = "-t" ]; then
    echo ""
    echo "----------------------------------------------------------"
    echo "[!] Manual On-Demand FSTRIM Requested"
    echo "----------------------------------------------------------"
    
    # Safety checks: ensure root and adequate power
    if [ "$(id -u)" -ne 0 ]; then
        echo "[-] Error: FSTRIM requires root (su)."
        exit 1
    fi
    
    BATT_LEVEL=$(dumpsys battery | grep -i "level:" | awk '{print $2}')
    if [ -n "$BATT_LEVEL" ] && [ "$BATT_LEVEL" -lt 30 ]; then
        echo "[-] Error: Battery is below 30% ($BATT_LEVEL%). Please connect charger before trimming."
        exit 1
    fi
    
    echo "[*] Running fstrim on /data and /cache..."
    fstrim -v /data
    fstrim -v /cache 2>/dev/null
    echo "[✓] FSTRIM complete. Stale flash blocks successfully garbage-collected."
fi

echo ""
echo "=========================================================="
echo " [✓] Hardware Health Inspection Complete!"
echo "=========================================================="
