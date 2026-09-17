#!/system/bin/sh
# Early boot service executed before Zygote starts

MODDIR=${0%/*}
LOGFILE="$MODDIR/experience_suite.log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] post-fs-data started" > "$LOGFILE"

# 1. Bind-mount floating_feature.xml (Hardware & Framework capabilities)
if [ -f "$MODDIR/system/etc/floating_feature.xml" ]; then
    chmod 0644 "$MODDIR/system/etc/floating_feature.xml"
    chcon u:object_r:system_file:s0 "$MODDIR/system/etc/floating_feature.xml" 2>/dev/null
    mount -o bind "$MODDIR/system/etc/floating_feature.xml" /system/etc/floating_feature.xml
    echo "Mounted floating_feature.xml successfully" >> "$LOGFILE"
fi

# Resetprop to unlock Camera Shutter Sound
resetprop ro.vendor.cam.name M1


# 2. Bind-mount CSC Features (OMC encrypted cscfeature.xml)
CODER="$MODDIR/bin/sec-omc-coder"
chmod 755 "$CODER"

CSC=$(getprop ro.csc.sales_code)
[ -z "$CSC" ] && CSC=$(getprop persist.omc.sales_code)
[ -z "$CSC" ] && CSC=$(getprop ril.official_csc)
echo "Active CSC: $CSC" >> "$LOGFILE"

CANDIDATES=""
if [ -n "$CSC" ]; then
    CANDIDATES="$CANDIDATES $(find /optics /prism -type f -name "cscfeature.xml" 2>/dev/null | grep -i "/$CSC/")"
fi
CANDIDATES="$CANDIDATES $(find /optics/configs/carriers -type f -name "cscfeature.xml" 2>/dev/null)"
CANDIDATES="$CANDIDATES $(find /prism/etc/carriers -type f -name "cscfeature.xml" 2>/dev/null)"

TARGETS=$(echo "$CANDIDATES" | tr ' ' '\n' | sort -u | grep -v '^$')

mkdir -p "$MODDIR/cache"

for TARGET in $TARGETS; do
    echo "Processing target: $TARGET" >> "$LOGFILE"
    HASH=$(echo -n "$TARGET" | md5sum | cut -d' ' -f1)
    DECODED="$MODDIR/cache/decoded_${HASH}.xml"
    PATCHED="$MODDIR/cache/patched_${HASH}.xml"
    ENCODED="$MODDIR/cache/encoded_${HASH}.bin"

    # Decode OMC
    cat "$TARGET" | "$CODER" -d 2>/dev/null | gzip -dc > "$DECODED" 2>/dev/null

    if ! grep -q "<FeatureSet>" "$DECODED" 2>/dev/null; then
        if grep -q "<FeatureSet>" "$TARGET" 2>/dev/null; then
            cp -f "$TARGET" "$DECODED"
        else
            echo "Failed to decode $TARGET" >> "$LOGFILE"
            continue
        fi
    fi

    # Check if already patched with all required features
    if grep -q "CscFeature_VoiceCall_ConfigRecording" "$DECODED" && grep -q "CscFeature_Common_SupportZProjectFunctionInGlobal" "$DECODED" && grep -q "CscFeature_Camera_ShutterSoundMenu" "$DECODED"; then
        echo "Already contains full feature set: $TARGET" >> "$LOGFILE"
    else
        echo "Injecting full feature set into $TARGET" >> "$LOGFILE"
        awk '/<\/FeatureSet>/{
            print "    <CscFeature_Setting_SupportRealTimeNetworkSpeed>TRUE</CscFeature_Setting_SupportRealTimeNetworkSpeed>"
            print "    <CscFeature_SystemUI_SupportRealTimeNetworkSpeed>TRUE</CscFeature_SystemUI_SupportRealTimeNetworkSpeed>"
            print "    <CscFeature_Common_SupportZProjectFunctionInGlobal>TRUE</CscFeature_Common_SupportZProjectFunctionInGlobal>"
            print "    <CscFeature_VoiceCall_ConfigRecording>RecordingAllowed</CscFeature_VoiceCall_ConfigRecording>"
            print "    <CscFeature_Camera_ShutterSoundMenu>TRUE</CscFeature_Camera_ShutterSoundMenu>"
            print "    <CscFeature_VoiceCall_SupportCallProtect>TRUE</CscFeature_VoiceCall_SupportCallProtect>"
        }1' "$DECODED" > "$PATCHED"
        mv -f "$PATCHED" "$DECODED"
    fi

    # Re-encode to OMC
    cat "$DECODED" | gzip -nc | "$CODER" -e > "$ENCODED" 2>/dev/null

    if [ -s "$ENCODED" ]; then
        chmod 0644 "$ENCODED"
        chcon --reference="$TARGET" "$ENCODED" 2>/dev/null || chcon u:object_r:vendor_configs_file:s0 "$ENCODED" 2>/dev/null
        mount -o bind "$ENCODED" "$TARGET"
        echo "Successfully bind-mounted $ENCODED -> $TARGET" >> "$LOGFILE"
    else
        echo "Encoding failed for $TARGET" >> "$LOGFILE"
    fi
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] post-fs-data finished" >> "$LOGFILE"
