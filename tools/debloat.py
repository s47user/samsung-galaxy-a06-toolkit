#!/usr/bin/env python3
"""
debloat.py - Precision Debloater & System Optimizer for Samsung Galaxy A06 (SM-A065F)
Base Firmware: A065FXXS4AYE2 (Android 14 / One UI Core 6.1)
"""

import os
import shutil
import sys
import time

SYSTEM_DIR = "work_rom/partitions/system_extracted/system"
PRODUCT_DIR = "work_rom/partitions/product_extracted"
LOG_FILE = "work_rom/debloat_audit.log"

# --- Master Debloat Manifest ---

REMOVE_SYSTEM_APP = [
    # Security Policy Distribution Channel (Not marketing telemetry)
    "DsmsAPK",  # Device Security Management Service (SELinux policy updater)

    # Telemetry, Marketing & Adware
    "AutomationTest_FB",
    "BBCAgent",
    "DAAgent",
    "FBAppManager_NS",
    "KidsHome_Installer",
    "MDMApp",
    "Rampart",
    "SafetyInformation",
    "UniversalMDMClient",
    "WebManual",

    # Foreign TTS Voices (Keeping English en_US)
    "SamsungTTSVoice_de_DE_f00",
    "SamsungTTSVoice_en_GB_f00",
    "SamsungTTSVoice_es_ES_f00",
    "SamsungTTSVoice_es_US_f00",
    "SamsungTTSVoice_fr_FR_f00",
    "SamsungTTSVoice_hi_IN_f00",
    "SamsungTTSVoice_it_IT_f00",
    "SamsungTTSVoice_pl_PL_f00",
    "SamsungTTSVoice_ru_RU_f00",
    "SamsungTTSVoice_th_TH_f00",
    "SamsungTTSVoice_vi_VN_f00",

    # Cosmetic & Stickers
    "SamSungStickerSource",
    "StickerCenter",

    # Dead Code & Hardware-Irrelevant Bloat (Zero Loss)
    "HandwritingService",     # S-Pen engine (no digitizer IC on A06)
    "BluetoothMidiService",   # Musical instrument BLE stack
    "EasterEgg",              # Android 14 Easter egg
    "BasicDreams",            # Daydream screensaver (LCD backlight power waste)
    "AllShareAware",          # Legacy DLNA Wi-Fi multicast pings
    "GooglePrintRecommendationService", # Cloud print discovery
    "SmartSwitchAgent",       # Device migration agent
    # NOTE: SmartSwitchStub is explicitly PRESERVED in CRITICAL_PROTECTED
    # to prevent SecSetupWizard_Global from throwing ActivityNotFoundException
    "HiyaService",            # Cloud spam caller ID (telemetry to Hiya servers)

    # Downstream Orphans (Safe Removals)
    "Traceur",                # Perfetto user-space system tracing UI
]

REMOVE_SYSTEM_PRIV_APP = [
    # Facebook Bloat
    "FBInstaller_NS",
    "FBServices",
    "serviceModeApp_FB",

    # Throttling
    "GameOptimizingService",  # GOS

    # Telemetry, Logging & OTA Updates
    "DeviceQualityAgent31",
    "DiagMonAgent91",
    "FotaAgent",  # OTA update agent (Manual firmware tracking required)
    "ImsLogger",
    "LogWriter",
    "RubinVersion34",
    "SCPMAgent",
    "SHClient",
    "SOAgent7",
    "SPPPushClient",

    # Key Attestation & Hardware Security (Inert on Knox 0x1)
    "SKMSAgent",  # Samsung Key Management Service (eSE key attestation)

    # Antivirus (McAfee Disk Scanner)
    "SmartManager_v6_DeviceSecurity",

    # Dead Knox Userspace Services
    "KLMSAgent",
    "KPECore",
    "KnoxCore",
    "KnoxGuard",
    "KnoxNetworkFilter",
    "KnoxZtFramework",
    "knoxvpnproxyhandler",
    # Note: SecAppSeparation powers Dual Messenger (WhatsApp/Telegram cloning).
    # Removed here for minimum footprint; preserve if dual apps are required.
    "SecAppSeparation",

    # Samsung Account & Galaxy Store Ecosystem
    "GalaxyApps_OPEN",
    "SamsungAccount",
    "SamsungBilling",
    "SamsungCloudClient",
    "SamsungExperienceService",
    "SamsungPayStubMini",

    # Downstream Orphans (Samsung Account / Push / Store dependents)
    "Fmm",                          # Find My Mobile (dead without SamsungAccount/SPPPushClient)
    "ThemeCenter",                  # Orphan of DressRoom & GalaxyApps_OPEN
    "ThemeStore",                   # Orphan of DressRoom & GalaxyApps_OPEN
    "SamsungCoreServices",          # Orphan of SamsungAccount
    "SamsungCoreServices-Stub",     # Orphan of SamsungAccount

    # Continuity & Sharing Downstream Orphans
    "MCFDeviceSync",                # BLE device beacon scanner
    "ShareLive",                    # Quick Share IoT beacon bridge
    "SamsungMultiConnectivity",     # Orphan of MCFDeviceSync & ShareLive
    "SmartThingsKit",               # Orphan of MCFDeviceSync & ShareLive
    "SmartCallProvider",            # Orphan shell provider (HiyaService backend stripped)

    # Microsoft Bloat
    "OneDrive_Samsung_v3",

    # Cosmetic & Heavy Add-ons
    "CallBGProvider",
    "DecoPic",
    "DressRoom",
    "DynamicLockscreen",

    # V1.2 Additions: Dead Code, RAM & Disk I/O Savers
    "AppsEdgePanel_v3.2",
    "PeopleStripe",
    "SecureFolder",
    "DigitalWellbeing",
    "StoryService",
    # NOTE: CMHProvider is removed from blind debloat and isolated in CRITICAL_PROTECTED
    # to protect SecGallery2021 database provider resolution.
    "BuiltInPrintService",
    "SmartSwitchAssistant",
]

REMOVE_PRODUCT_APP = [
    # Heavy Google Apps (Installable from Play Store)
    "Duo",      # Google Meet
    "Gmail2",   # Gmail
    "Maps",     # Google Maps
    "YouTube",  # YouTube
]

REMOVE_PRODUCT_PRIV_APP = [
    # Google Assistant & Background Listeners
    "Velvet",                      # Google App / Assistant (~271 MB)
    "AndroidAutoStub",             # Android Auto
    "FamilyLinkParentalControls",  # Parental Controls
    "SearchSelector",

    # High RAM Consumer & Its Sandbox Orphan
    "AndroidSystemIntelligence",   # Contextual text/action ML daemon (~60-90MB PSS)
    "PrivateComputeServices",      # Sandbox cloud/device boundary for ASI (dead orphan)
]

# --- Strict Integrity Protection (Must Never Be Touched) ---
CRITICAL_PROTECTED = [
    # Hardware Vendor Drivers & Biometrics (CRITICAL: Do not touch vendor ICs)
    ("system/app", "sileadManager"),        # Silead Fingerprint/Touch IC controller vendor
    ("system/priv-app", "BiometricSetting"),
    ("system/priv-app", "SoundAlive_U"),

    # RIL & Telephony Stack
    ("system/priv-app", "SamsungDialer"),
    ("system/priv-app", "SamsungInCallUI"),
    ("system/priv-app", "Telecom"),
    ("system/priv-app", "TeleService"),
    ("system/priv-app", "imsservice"),
    ("system/priv-app", "MmsService"),
    ("system/priv-app", "SecTelephonyProvider"),

    # Camera with MTK ISP Calibration
    ("system/priv-app", "SamSungCamera"),

    # Core System & Framework
    ("system/priv-app", "SecSettings"),
    ("system/priv-app", "SettingsProvider"),
    ("system/priv-app", "SecSettingsIntelligence"),
    ("system/priv-app", "SecSetupWizard_Global"),
    ("system/app", "SmartSwitchStub"),      # Required intent receiver to prevent setup wizard loop

    # Gallery Media Backend (Protects SecGallery from NullPointerException)
    ("system/priv-app", "CMHProvider"),

    # Keyboard & Launcher
    ("system/app", "HoneyBoard"),
    ("system/priv-app", "TouchWizHome_2017"),

    # Google Core Foundations
    ("product/priv-app", "GmsCore"),
    ("product/priv-app", "Phonesky"),
    ("product/app", "WebViewGoogle"),
    ("product/app", "TrichromeLibrary"),
]

PERFORMANCE_PROPS = """
# ====================================================================
# Custom ROM Optimizations - Samsung Galaxy A06 (Helio G85 / One UI 6)
# ====================================================================

# --- SurfaceFlinger & Rendering Pipeline ---
debug.sf.disable_backpressure=1
ro.surface_flinger.has_wide_color_display=false
ro.surface_flinger.has_HDR_display=false
debug.hwui.renderer=skiagl

# --- RAM & Dalvik VM Tuning (4GB Profile) ---
dalvik.vm.heapgrowthlimit=192m
dalvik.vm.heapsize=512m
dalvik.vm.heaptargetutilization=0.75
dalvik.vm.heapminfree=2m
dalvik.vm.heapmaxfree=8m
pm.dexopt.boot-image=verify
pm.dexopt.install=speed-profile
dalvik.vm.dex2oat-threads=4

# --- Disabling Telemetry, Dumps & Verbose Logging ---
profiler.force_disable_err_rpt=true
profiler.force_disable_ulog=true
ro.logd.size=64K
ro.config.knox=0
ro.config.dmverity=false
persist.sys.strictmode.disable=true
persist.sys.gos.support=0

# --- Telephony & Radio Latency ---
ro.telephony.call_ring.delay=0
ro.ril.fast.dormancy.rule=1
"""

def get_dir_size(d):
    total = 0
    for root, dirs, files in os.walk(d, followlinks=False):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.lstat(fp).st_size
            except OSError:
                pass
    return total

def remove_targets(base_path, targets, label, log_lines):
    removed_count = 0
    bytes_saved = 0
    for target in targets:
        target_path = os.path.join(base_path, target)
        if os.path.exists(target_path):
            sz = get_dir_size(target_path)
            try:
                if os.path.isdir(target_path):
                    shutil.rmtree(target_path)
                else:
                    os.remove(target_path)
                removed_count += 1
                bytes_saved += sz
                msg = f"  [-] [{label}] Removed: {target:<35} ({sz / (1024*1024):>6.2f} MB)"
                print(msg)
                log_lines.append(msg)
            except Exception as e:
                err_msg = f"  [!] Error removing {target_path}: {e}"
                print(err_msg)
                log_lines.append(err_msg)
        else:
            log_lines.append(f"  [?] [{label}] Not present: {target}")
    return removed_count, bytes_saved

def verify_protected():
    print("\n[+] Running Critical Component Protection Audit...")
    all_ok = True
    base_map = {
        "system/app": os.path.join(SYSTEM_DIR, "app"),
        "system/priv-app": os.path.join(SYSTEM_DIR, "priv-app"),
        "product/app": os.path.join(PRODUCT_DIR, "app"),
        "product/priv-app": os.path.join(PRODUCT_DIR, "priv-app"),
    }
    for sub, name in CRITICAL_PROTECTED:
        full = os.path.join(base_map[sub], name)
        if os.path.exists(full):
            print(f"  [✓] Verified INTACT: {sub}/{name}")
        else:
            print(f"  [✗] CRITICAL ALERT: Missing protected component: {sub}/{name}!")
            all_ok = False
    return all_ok

def apply_build_props(log_lines):
    prop_path = os.path.join(SYSTEM_DIR, "build.prop")
    if not os.path.exists(prop_path):
        print("[-] Error: build.prop not found!")
        return False

    with open(prop_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if "persist.sys.gos.support=0" in content:
        print("[+] Performance properties already present in build.prop.")
        return True

    with open(prop_path, "a", encoding="utf-8") as f:
        f.write("\n" + PERFORMANCE_PROPS + "\n")

    msg = "[+] Successfully injected performance & Knox-disabling flags into build.prop"
    print(msg)
    log_lines.append(msg)
    return True

def main():
    print("==========================================================")
    print(" Samsung Galaxy A06 (SM-A065F) Precision Debloat Engine")
    print("==========================================================\n")

    log_lines = [
        f"Debloat Execution Audit - {time.ctime()}",
        f"Target Firmware: A065FXXS4AYE2",
        "----------------------------------------------------------"
    ]

    total_removed = 0
    total_bytes = 0

    # 1. Debloat system/app
    print("[1/4] Processing system/app...")
    cnt, sz = remove_targets(os.path.join(SYSTEM_DIR, "app"), REMOVE_SYSTEM_APP, "system/app", log_lines)
    total_removed += cnt
    total_bytes += sz

    # 2. Debloat system/priv-app
    print("\n[2/4] Processing system/priv-app...")
    cnt, sz = remove_targets(os.path.join(SYSTEM_DIR, "priv-app"), REMOVE_SYSTEM_PRIV_APP, "system/priv-app", log_lines)
    total_removed += cnt
    total_bytes += sz

    # 3. Debloat product/app
    print("\n[3/4] Processing product/app...")
    cnt, sz = remove_targets(os.path.join(PRODUCT_DIR, "app"), REMOVE_PRODUCT_APP, "product/app", log_lines)
    total_removed += cnt
    total_bytes += sz

    # 4. Debloat product/priv-app
    print("\n[4/4] Processing product/priv-app...")
    cnt, sz = remove_targets(os.path.join(PRODUCT_DIR, "priv-app"), REMOVE_PRODUCT_PRIV_APP, "product/priv-app", log_lines)
    total_removed += cnt
    total_bytes += sz

    # 5. Inject Performance Properties
    print("\n[5/5] Injecting performance tuning to build.prop...")
    apply_build_props(log_lines)

    # 6. Verify Protection
    if not verify_protected():
        print("\n[!] WARNING: One or more protected critical packages were missing!")
    else:
        print("\n[✓] 100% Core Protection Verified: All telephony, camera, keyboard, and framework components intact.")

    summary = (
        f"\n==========================================================\n"
        f" DEBLOAT COMPLETE SUMMARY:\n"
        f" Total Packages Removed : {total_removed}\n"
        f" Total Storage Saved    : {total_bytes / (1024*1024):.2f} MB ({total_bytes / (1024**3):.2f} GB)\n"
        f"=========================================================="
    )
    print(summary)
    log_lines.append(summary)

    with open(LOG_FILE, "w", encoding="utf-8") as lf:
        lf.write("\n".join(log_lines) + "\n")
    print(f"[+] Complete audit log written to: {LOG_FILE}\n")

if __name__ == "__main__":
    main()
