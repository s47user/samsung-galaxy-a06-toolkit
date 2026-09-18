#!/usr/bin/env bash
# ==============================================================================
# backup_efs_nvram.sh — Samsung Galaxy A06 (SM-A065F / MT6769V Helio G85)
# Precision IMEI, EFS, NVRAM, and Baseband Calibration Backup Tool
# ==============================================================================

set -eo pipefail

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUT_DIR="backups/imei_efs_${TIMESTAMP}"
DEVICE_TMP="/data/local/tmp/imei_backup_${TIMESTAMP}"

# Partitions containing IMEI, MAC addresses, RF calibration, and EFS credentials
PARTITIONS=(
    "efs"       # Samsung EFS (IMEI, provisioning keys)
    "sec_efs"   # Samsung Secondary EFS
    "nvram"     # MediaTek NVRAM (Core RF calibration & IMEI storage)
    "nvdata"    # MediaTek NV Data filesystem (/mnt/vendor/nvdata)
    "nvcfg"     # MediaTek Carrier / NV configuration
    "protect1"  # MediaTek Protect F (Factory RF calibration)
    "protect2"  # MediaTek Protect S (Runtime RF parameters)
    "proinfo"   # Device Serial Number, hardware barcodes
    "sec1"      # Security partition
    "seccfg"    # Security lock configuration
)

echo "=========================================================="
echo " Samsung Galaxy A06 (SM-A065F) IMEI / NV Backup Engine"
echo "=========================================================="

if ! command -v adb &>/dev/null; then
    echo "[-] Error: 'adb' command not found in PATH."
    exit 1
fi

echo "[*] Checking ADB device connection..."
adb wait-for-device
DEVICE_STATE=$(adb get-state 2>/dev/null || echo "offline")
if [ "$DEVICE_STATE" != "device" ]; then
    echo "[-] Error: Device not ready (state: $DEVICE_STATE)."
    exit 1
fi

echo "[+] Device detected. Verifying root permissions (KernelSU / Magisk / APatch)..."
IS_ROOT=$(adb shell "su -c 'id -u'" 2>/dev/null | tr -d '\r\n')
if [ "$IS_ROOT" != "0" ]; then
    echo "[-] Error: Root access is required to dump raw block devices."
    echo "    Please grant root access in KernelSU/Magisk/APatch manager on your phone screen."
    exit 1
fi

echo "[+] Root confirmed (uid=0)."
mkdir -p "$OUT_DIR"

echo "[*] Preparing device staging directory: $DEVICE_TMP..."
adb shell "su -c 'mkdir -p $DEVICE_TMP'"

echo "[*] Dumping critical identity and calibration partitions:"
for PART in "${PARTITIONS[@]}"; do
    printf "  -> Dumping %-10s ... " "$PART"
    adb shell "su -c '
        BLK=/dev/block/by-name/$PART
        if [ -b \"\$BLK\" ]; then
            dd if=\"\$BLK\" of=\"$DEVICE_TMP/${PART}.img\" bs=4096 status=none
            chmod 644 \"$DEVICE_TMP/${PART}.img\"
            echo OK
        else
            echo MISSING
        fi
    '" | tr -d '\r'
done

echo "[*] Packaging archive on device..."
adb shell "su -c 'cd $DEVICE_TMP && tar -czf backup_payload.tar.gz *.img && sha256sum *.img > checksums.sha256'"

echo "[*] Pulling backup archive to workstation: $OUT_DIR..."
adb pull "$DEVICE_TMP/backup_payload.tar.gz" "$OUT_DIR/a06_imei_efs_backup_${TIMESTAMP}.tar.gz"
adb pull "$DEVICE_TMP/checksums.sha256" "$OUT_DIR/checksums.sha256"

echo "[*] Cleaning up temporary device files..."
adb shell "su -c 'rm -rf $DEVICE_TMP'"

echo "[*] Computing local SHA-256 integrity check..."
(cd "$OUT_DIR" && sha256sum "a06_imei_efs_backup_${TIMESTAMP}.tar.gz" > "archive_sha256.txt")

echo ""
echo "=========================================================="
echo " [✓] IMEI & EFS BACKUP COMPLETED SUCCESSFULLY!"
echo "=========================================================="
echo " Location: $(pwd)/$OUT_DIR"
echo " Files:"
ls -lh "$OUT_DIR"
echo "=========================================================="
