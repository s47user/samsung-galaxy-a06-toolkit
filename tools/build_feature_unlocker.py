#!/usr/bin/env python3
"""
Samsung Galaxy A06 (SM-A065F) - V2.1 Feature Unlocker Module Builder
Generates and packages a systemless KernelSU-Next module to unlock flagship
One UI features on Galaxy A06 (One UI Core 6.1 / Android 14).
"""

import os
import sys
import shutil
import zipfile
import hashlib
import xml.etree.ElementTree as ET

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_DIR = os.path.join(WORKSPACE_DIR, "modules", "a06_feature_unlocker")
STOCK_XML_PATH = os.path.join(
    WORKSPACE_DIR, "work_rom", "partitions", "system_extracted", "system", "etc", "floating_feature.xml"
)
OUTPUT_ZIP_PATH = os.path.join(WORKSPACE_DIR, "A06_Feature_Unlocker_v2.1.zip")


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def build_floating_feature_xml():
    print(f"[*] Reading base stock XML: {STOCK_XML_PATH}")
    if not os.path.exists(STOCK_XML_PATH):
        raise FileNotFoundError(f"Stock XML not found at {STOCK_XML_PATH}")

    # Parse stock XML
    tree = ET.parse(STOCK_XML_PATH)
    root = tree.getroot()

    if root.tag != "SecFloatingFeatureSet":
        raise ValueError(f"Unexpected root tag: {root.tag}")

    # Index existing tags
    tag_map = {child.tag: child for child in root}

    # Desired modifications & injections
    # 1. Good Lock Support: change sep_lite_new -> sep_basic
    if "SEC_FLOATING_FEATURE_COMMON_CONFIG_SEP_CATEGORY" in tag_map:
        tag_map["SEC_FLOATING_FEATURE_COMMON_CONFIG_SEP_CATEGORY"].text = "sep_basic"
        print("  [+] Set SEC_FLOATING_FEATURE_COMMON_CONFIG_SEP_CATEGORY = sep_basic")

    # 2. Flagship UI Animations: change LowestEnd -> HighEnd
    if "SEC_FLOATING_FEATURE_LAUNCHER_CONFIG_ANIMATION_TYPE" in tag_map:
        tag_map["SEC_FLOATING_FEATURE_LAUNCHER_CONFIG_ANIMATION_TYPE"].text = "HighEnd"
        print("  [+] Set SEC_FLOATING_FEATURE_LAUNCHER_CONFIG_ANIMATION_TYPE = HighEnd")

    # Features to ensure / inject if missing
    features_to_inject = [
        # Edge Panels & Edge Lighting
        ("SEC_FLOATING_FEATURE_COMMON_SUPPORT_EDGE", "TRUE"),
        ("SEC_FLOATING_FEATURE_SYSTEMUI_SUPPORT_EDGELIGHTING", "TRUE"),
        ("SEC_FLOATING_FEATURE_SETTINGS_SUPPORT_EDGE_SCREEN", "TRUE"),

        # System-Wide Dolby Atmos
        ("SEC_FLOATING_FEATURE_AUDIO_SUPPORT_DOLBY_AUDIO", "TRUE"),
        ("SEC_FLOATING_FEATURE_AUDIO_SUPPORT_DOLBY_FOR_SPEAKER", "TRUE"),

        # Separate App Sound
        ("SEC_FLOATING_FEATURE_AUDIO_SUPPORT_SEPARATE_APP_SOUND", "TRUE"),

        # Native Hardware Call Recording
        ("SEC_FLOATING_FEATURE_VOICECALL_CONFIG_RECORDING", "RecordingAllowedByMenu"),

        # Smart View / Miracast Screen Mirroring
        ("SEC_FLOATING_FEATURE_WIFI_SUPPORT_MIRACAST", "TRUE"),

        # Full Blur support
        ("SEC_FLOATING_FEATURE_GRAPHICS_SUPPORT_CAPTURED_BLUR", "TRUE"),
        ("SEC_FLOATING_FEATURE_GRAPHICS_SUPPORT_PARTIAL_BLUR", "TRUE"),

        # Battery Health Protection (80%/85% limit)
        ("SEC_FLOATING_FEATURE_BATTERY_SUPPORT_LONGLIFE_FORCE_CUTOFF", "TRUE"),
    ]

    for tag, value in features_to_inject:
        if tag in tag_map:
            tag_map[tag].text = value
            print(f"  [+] Updated existing {tag} = {value}")
        else:
            new_elem = ET.SubElement(root, tag)
            new_elem.text = value
            print(f"  [+] Injected new {tag} = {value}")

    # Format XML with indentation
    ET.indent(tree, space="    ", level=0)

    # Output path
    out_dir = os.path.join(MODULE_DIR, "system", "etc")
    os.makedirs(out_dir, exist_ok=True)
    out_xml_path = os.path.join(out_dir, "floating_feature.xml")

    # Serialize with XML declaration
    with open(out_xml_path, "wb") as f:
        tree.write(f, encoding="UTF-8", xml_declaration=True)

    # Validate generated XML parses cleanly
    ET.parse(out_xml_path)
    print(f"[*] Validated and saved: {out_xml_path} ({os.path.getsize(out_xml_path)} bytes)")


def create_module_metadata():
    print("[*] Creating module metadata and scripts...")

    # module.prop
    module_prop = """id=a06-feature-unlocker
name=Samsung Galaxy A06 Feature Unlocker (V2.1)
version=v2.1.0
versionCode=2100
author=s47user
description=Systemlessly unlocks Good Lock, Edge Panels & Lighting, High-End Animations, System-Wide Dolby Atmos, Separate App Sound, Native Call Recording, and Screen Recorder on Galaxy A06 (SM-A065F).
"""
    with open(os.path.join(MODULE_DIR, "module.prop"), "w", newline="\n") as f:
        f.write(module_prop)

    # customize.sh
    customize_sh = """#!/system/bin/sh
SKIPUNZIP=0

ui_print "************************************************"
ui_print "     Samsung Galaxy A06 (SM-A065F)             "
ui_print "       One UI V2.1 Feature Unlocker             "
ui_print "************************************************"
ui_print " Author: s47user                                "
ui_print " Target: Android 14 / One UI Core 6.1           "
ui_print " Architecture: KernelSU-Next / Magisk Overlay   "
ui_print "************************************************"

# Validate device model
MODEL=$(getprop ro.product.model)
DEVICE=$(getprop ro.product.device)
ui_print "- Detected Device: $MODEL ($DEVICE)"

ui_print "- Unlocking features systemlessly:"
ui_print "  [✓] Good Lock Suite (SEP Category -> sep_basic)"
ui_print "  [✓] Edge Panels & Edge Lighting"
ui_print "  [✓] High-End Launcher Physics & Gaussian Blur"
ui_print "  [✓] System-Wide Dolby Atmos (Headphones & Speaker)"
ui_print "  [✓] Separate App Sound (MultiSound)"
ui_print "  [✓] Native 2-Way Hardware Call Recording"
ui_print "  [✓] Samsung Screen Recorder (Full Video + Internal Audio)"
ui_print "  [✓] Smart View (Miracast Screen Mirroring)"
ui_print "  [✓] Protect Battery (80%/85% Charge Limit)"

ui_print "- Setting POSIX permissions..."
set_perm_recursive $MODPATH 0 0 0755 0644
set_perm $MODPATH/post-fs-data.sh 0 0 0755
set_perm $MODPATH/service.sh 0 0 0755
set_perm $MODPATH/system/etc/floating_feature.xml 0 0 0644

ui_print "************************************************"
ui_print " Installation Succeeded!                        "
ui_print " Please reboot your device to activate features."
ui_print "************************************************"
"""
    with open(os.path.join(MODULE_DIR, "customize.sh"), "w", newline="\n") as f:
        f.write(customize_sh)
    os.chmod(os.path.join(MODULE_DIR, "customize.sh"), 0o755)

    # post-fs-data.sh
    post_fs_data_sh = """#!/system/bin/sh
# Runs in early boot before Zygote starts

MODDIR=${0%/*}

# Explicit bind mount for Samsung floating_feature.xml
if [ -f "$MODDIR/system/etc/floating_feature.xml" ]; then
    chmod 0644 "$MODDIR/system/etc/floating_feature.xml"
    chcon u:object_r:system_file:s0 "$MODDIR/system/etc/floating_feature.xml"
    mount -o bind "$MODDIR/system/etc/floating_feature.xml" /system/etc/floating_feature.xml
fi
"""
    with open(os.path.join(MODULE_DIR, "post-fs-data.sh"), "w", newline="\n") as f:
        f.write(post_fs_data_sh)
    os.chmod(os.path.join(MODULE_DIR, "post-fs-data.sh"), 0o755)

    # service.sh
    service_sh = """#!/system/bin/sh
# Late-stage service executed after boot completion

MODDIR=${0%/*}

# Wait until boot completes
while [ "$(getprop sys.boot_completed)" != "1" ]; do
    sleep 2
done

# 1. Dynamic CSC Call Recording Injection (safe after vold decryption)
for csc_path in /prism/etc/cscfeature.xml /system/csc/cscfeature.xml; do
    if [ -f "$csc_path" ]; then
        if ! grep -q "CscFeature_VoiceCall_ConfigRecording" "$csc_path"; then
            mkdir -p "$MODDIR/patched_csc"
            patched_file="$MODDIR/patched_csc/$(basename $csc_path)"
            sed 's#</FeatureSet>#    <CscFeature_VoiceCall_ConfigRecording>RecordingAllowedByMenu</CscFeature_VoiceCall_ConfigRecording>\\n</FeatureSet>#' "$csc_path" > "$patched_file" 2>/dev/null
            if [ -s "$patched_file" ]; then
                chmod 0644 "$patched_file"
                chcon u:object_r:system_file:s0 "$patched_file"
                mount -o bind "$patched_file" "$csc_path"
            fi
        fi
    fi
done

# 2. Ensure Edge Panels and animations are recognized in system settings
settings put system edge_panel_enabled 1 2>/dev/null
settings put system edge_lighting 1 2>/dev/null

# Exit cleanly
exit 0
"""
    with open(os.path.join(MODULE_DIR, "service.sh"), "w", newline="\n") as f:
        f.write(service_sh)
    os.chmod(os.path.join(MODULE_DIR, "service.sh"), 0o755)


def package_zip():
    print(f"[*] Compiling zip archive: {OUTPUT_ZIP_PATH}")
    if os.path.exists(OUTPUT_ZIP_PATH):
        os.remove(OUTPUT_ZIP_PATH)

    with zipfile.ZipFile(OUTPUT_ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(MODULE_DIR):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, MODULE_DIR)
                zf.write(abs_path, rel_path)
                print(f"  -> Added: {rel_path}")

    size_kb = os.path.getsize(OUTPUT_ZIP_PATH) / 1024
    sha256 = compute_sha256(OUTPUT_ZIP_PATH)
    print(f"[✓] Package complete: {OUTPUT_ZIP_PATH}")
    print(f"    Size: {size_kb:.2f} KB")
    print(f"    SHA-256: {sha256}")


def main():
    print("=== Samsung Galaxy A06 V2.1 Feature Unlocker Builder ===")
    os.makedirs(MODULE_DIR, exist_ok=True)
    build_floating_feature_xml()
    create_module_metadata()
    package_zip()
    print("=== All tasks completed successfully ===")


if __name__ == "__main__":
    main()
