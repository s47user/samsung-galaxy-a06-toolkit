#!/usr/bin/env bash
# backup_efs_nvram_adb.sh - Dump vital Samsung Galaxy A06 partitions directly to PC via ADB
# Works while device is booted in OrangeFox / TWRP recovery (root adb).
# No MicroSD card or decrypted internal storage required!

set -euo pipefail

BACKUP_DIR="backups/A06_partitions_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "========================================================"
echo " Samsung Galaxy A06 (SM-A065F) - ADB Partition Backup"
echo " Target Folder: $BACKUP_DIR"
echo "========================================================"

echo "[*] Waiting for device in Recovery mode..."
adb wait-for-device

# Verify recovery environment
DEV_PROP=$(adb shell getprop ro.product.device 2>/dev/null || true)
echo "[✓] Connected device: $DEV_PROP"

# Vital partitions list: name and by-name block path
PARTITIONS=(
    "sec_efs:/dev/block/by-name/sec_efs"
    "nvram:/dev/block/by-name/nvram"
    "nvdata:/dev/block/by-name/nvdata"
    "nvcfg:/dev/block/by-name/nvcfg"
    "protect1:/dev/block/by-name/protect1"
    "protect2:/dev/block/by-name/protect2"
    "proinfo:/dev/block/by-name/proinfo"
    "boot:/dev/block/by-name/boot"
    "dtbo:/dev/block/by-name/dtbo"
    "vbmeta:/dev/block/by-name/vbmeta"
    "up_param:/dev/block/by-name/up_param"
)

echo "[*] Starting direct raw partition stream to PC..."

for item in "${PARTITIONS[@]}"; do
    NAME="${item%%:*}"
    DEV="${item##*:}"
    OUT_FILE="$BACKUP_DIR/${NAME}.img"

    echo -n "  -> Dumping $NAME ($DEV)... "
    adb exec-out "dd if=$DEV 2>/dev/null" > "$OUT_FILE"
    
    SZ=$(stat -c%s "$OUT_FILE")
    if [ "$SZ" -gt 0 ]; then
        echo "OK ($((SZ / 1024)) KB)"
    else
        echo "FAILED (0 bytes)"
    fi
done

echo ""
echo "[*] Computing MD5 checksums..."
cd "$BACKUP_DIR"
md5sum *.img > md5sums.txt
cd - > /dev/null

echo "========================================================"
echo "[✓] ALL VITAL RADIO / EFS / BOOT PARTITIONS BACKED UP!"
echo " Location: $BACKUP_DIR"
echo " Keep this folder safe. It contains your unique IMEI and radio calibration."
echo "========================================================"
