#!/system/bin/sh
# ==============================================================================
# a06_backup_efs.sh - One-Tap EFS / NVRAM / Radio Partition Backup Guardian
# Target: Samsung Galaxy A06 (SM-A065F / SM-A065M)
# SoC: MediaTek Helio G85 | OS: Android 14 / One UI Core 6.1
# ==============================================================================

if [ "$(id -u)" -ne 0 ]; then
    echo "[-] Error: This script must be run as root (su)."
    exit 1
fi

echo "=========================================================="
echo " Samsung Galaxy A06 — EFS & NVRAM Radio Guardian Backup"
echo " Bit-for-bit cryptographic snapshot of IMEI & radio data"
echo "=========================================================="

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/sdcard/EFS_Backups"
STAGING_DIR="/data/local/tmp/efs_backup_staging_${DATE}"

mkdir -p "$BACKUP_DIR"
mkdir -p "$STAGING_DIR"

PARTITIONS="efs sec_efs nvram nvdata nvcfg protect1 protect2"
SUCCESS_COUNT=0

echo "[*] Dumping critical radio & IMEI partitions..."

for PART in $PARTITIONS; do
    NODE="/dev/block/by-name/$PART"
    if [ -b "$NODE" ]; then
        echo "  -> Dumping $PART ($NODE)..."
        dd if="$NODE" of="$STAGING_DIR/${PART}.img" bs=4096 2>/dev/null
        if [ -s "$STAGING_DIR/${PART}.img" ]; then
            sha256sum "$STAGING_DIR/${PART}.img" >> "$STAGING_DIR/sha256sums.txt"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        fi
    else
        echo "  [!] Warning: $NODE not found. Checking platform paths..."
        ALT_NODE=$(find /dev/block/platform -name "$PART" 2>/dev/null | head -n 1)
        if [ -n "$ALT_NODE" ] && [ -b "$ALT_NODE" ]; then
            echo "  -> Dumping $PART ($ALT_NODE)..."
            dd if="$ALT_NODE" of="$STAGING_DIR/${PART}.img" bs=4096 2>/dev/null
            sha256sum "$STAGING_DIR/${PART}.img" >> "$STAGING_DIR/sha256sums.txt"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        fi
    fi
done

if [ "$SUCCESS_COUNT" -eq 0 ]; then
    echo "[-] Error: No radio partitions could be dumped. Aborting."
    rm -rf "$STAGING_DIR"
    exit 1
fi

# Package into compressed tarball
ARCHIVE="$BACKUP_DIR/EFS_NVRAM_A065F_${DATE}.tar.gz"
echo ""
echo "[*] Packaging into compressed archive: $ARCHIVE..."
cd "$STAGING_DIR" && tar -czf "$ARCHIVE" *
rm -rf "$STAGING_DIR"

if [ -f "$ARCHIVE" ]; then
    ARCHIVE_SZ=$(ls -lh "$ARCHIVE" | awk '{print $5}')
    ARCHIVE_HASH=$(sha256sum "$ARCHIVE" | awk '{print $1}')
    
    echo ""
    echo "=========================================================="
    echo " [✓] EFS & NVRAM BACKUP CREATED SUCCESSFULLY!"
    echo " Location: $ARCHIVE ($ARCHIVE_SZ)"
    echo " SHA-256:  $ARCHIVE_HASH"
    echo "=========================================================="
    
    # Check for external MicroSD card and copy if present
    SD_CARD=$(ls -d /storage/????-???? 2>/dev/null | head -n 1)
    if [ -n "$SD_CARD" ] && [ -d "$SD_CARD" ]; then
        mkdir -p "$SD_CARD/EFS_Backups"
        cp -f "$ARCHIVE" "$SD_CARD/EFS_Backups/"
        echo "[+] Safety mirror copied to MicroSD: $SD_CARD/EFS_Backups/"
    fi
    
    echo ""
    echo "[!] CRITICAL: Please copy this backup file to your PC or Cloud storage!"
    echo "    To restore in the future, run: ./scripts/a06_restore_efs.sh $ARCHIVE"
    echo "=========================================================="
else
    echo "[-] Packaging failed!"
    exit 1
fi
