#!/system/bin/sh
# ==============================================================================
# a06_restore_efs.sh - One-Tap EFS / NVRAM / Radio Partition Restore Guardian
# Target: Samsung Galaxy A06 (SM-A065F / SM-A065M)
# SoC: MediaTek Helio G85 | OS: Android 14 / One UI Core 6.1
# ==============================================================================

if [ "$(id -u)" -ne 0 ]; then
    echo "[-] Error: This script must be run as root (su)."
    exit 1
fi

ARCHIVE="$1"
CONFIRM="$2"

echo "=========================================================="
echo " Samsung Galaxy A06 — EFS & NVRAM Radio Restore Tool"
echo " Restores bit-for-bit factory IMEI and cellular calibration"
echo "=========================================================="

if [ -z "$ARCHIVE" ] || [ ! -f "$ARCHIVE" ]; then
    echo "[-] Error: Please provide a valid backup archive path."
    echo "    Usage: $0 /sdcard/EFS_Backups/EFS_NVRAM_A065F_<DATE>.tar.gz [--yes]"
    exit 1
fi

if [ "$CONFIRM" != "--yes" ] && [ "$CONFIRM" != "-y" ]; then
    echo ""
    echo "[!] WARNING: This will overwrite current EFS and NVRAM partitions!"
    echo "    To execute the restore, add the --yes confirmation flag:"
    echo "    $0 $ARCHIVE --yes"
    echo ""
    exit 0
fi

STAGING_DIR="/data/local/tmp/efs_restore_staging_$$"
mkdir -p "$STAGING_DIR"

echo "[*] Extracting archive: $ARCHIVE..."
tar -xzf "$ARCHIVE" -C "$STAGING_DIR"

if [ ! -f "$STAGING_DIR/sha256sums.txt" ]; then
    echo "[-] Warning: No checksum verification manifest found in archive."
else
    echo "[*] Verifying cryptographic SHA-256 partition image integrity..."
    cd "$STAGING_DIR"
    if sha256sum -c sha256sums.txt; then
        echo "[+] Integrity check PASSED on all partition images!"
    else
        echo "[-] Error: Cryptographic checksum failed! Corrupt archive. Aborting for safety."
        rm -rf "$STAGING_DIR"
        exit 1
    fi
fi

PARTITIONS="efs sec_efs nvram nvdata nvcfg protect1 protect2"
RESTORED=0

echo ""
echo "[*] Flashing partition images back to hardware..."

for PART in $PARTITIONS; do
    SRC="$STAGING_DIR/${PART}.img"
    DST="/dev/block/by-name/$PART"
    
    if [ -f "$SRC" ]; then
        if [ -b "$DST" ]; then
            echo "  -> Restoring $PART ($DST)..."
            dd if="$SRC" of="$DST" bs=4096 2>/dev/null
            RESTORED=$((RESTORED + 1))
        else
            ALT_DST=$(find /dev/block/platform -name "$PART" 2>/dev/null | head -n 1)
            if [ -n "$ALT_DST" ] && [ -b "$ALT_DST" ]; then
                echo "  -> Restoring $PART ($ALT_DST)..."
                dd if="$SRC" of="$ALT_DST" bs=4096 2>/dev/null
                RESTORED=$((RESTORED + 1))
            else
                echo "  [-] Error: Block node for $PART not found!"
            fi
        fi
    fi
done

sync
rm -rf "$STAGING_DIR"

echo ""
echo "=========================================================="
echo " [✓] EFS & NVRAM RESTORE COMPLETED ($RESTORED partitions restored)!"
echo " Please reboot your device now to reload the cellular modem:"
echo "   reboot"
echo "=========================================================="
