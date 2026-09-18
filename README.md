# Samsung Galaxy A06 (SM-A065F) Master Development Toolkit

Unified engineering toolkit, custom kernel research, boot logo customization, and rooting procedures for the **Samsung Galaxy A06 (`SM-A065F`)** running **Android 14 / One UI Core 6.1 (MediaTek Helio G85 MT6769V)**.

[![Release](https://img.shields.io/github/v/release/s47user/android_kernel_samsung_a06?label=Kernel%20Release&color=blue)](https://github.com/s47user/android_kernel_samsung_a06/releases/latest)
[![KernelSU-Next](https://img.shields.io/badge/KernelSU--Next-v3.3.0-success)](https://github.com/rifsxd/KernelSU-Next)
[![Device](https://img.shields.io/badge/Device-SM--A065F%2FM-orange)](https://github.com/s47user/samsung-galaxy-a06-toolkit)
[![License](https://img.shields.io/badge/License-GPL%202.0-yellow.svg)](https://opensource.org/licenses/GPL-2.0)

---

## Device Profile
| Specification | Value |
| :--- | :--- |
| **Model** | Samsung Galaxy A06 (`SM-A065F`) |
| **SoC** | MediaTek Helio G85 (`MT6769V/CZ`) |
| **CPU** | 2x Cortex-A75 @ 2.0 GHz + 6x Cortex-A55 @ 1.8 GHz |
| **GPU** | ARM Mali-G52 2EEMC2 |
| **Display** | 720 × 1600 (20:9 Aspect Ratio) |
| **Storage** | eMMC 5.1 |
| **Filesystem** | EROFS (Dynamic Partitions inside `super.img`) |
| **Firmware Base** | `A065FXXS4AYE1` / Build `A065FXXS4AYE2` |
| **Kernel Version** | `4.19.191` (Non-GKI architecture, ramdisk in `boot.img`) |
| **Verified Boot** | AVB 2.0 (`vbmeta.img`) & Samsung Verified Boot (SVB) |

---

## Unified Repository Structure
```text
├── README.md                                # Master documentation
├── .gitignore                               # Binary, cache & firmware exclusions
├── boot_logo_stock/                         # Extracted stock Samsung A06 splash assets (26 images)
├── configs/
│   ├── custom.pif.prop                      # Play Integrity Fix spoofing configuration
│   └── physwizz_kernel_optimizations.config # Defconfig optimization matrix
├── docs/
│   ├── apatch_root_guide.md                 # Complete APatch flashing guide
│   ├── boot_logo_guide.md                   # Boot logo & bootloader warning customization
│   ├── custom_kernel_guide.md               # Kernel compilation & Physwizz methodology
│   └── performance_tuning.md                # eMMC bottleneck fixes & sysfs tuning
├── scripts/
│   ├── apply_safe_tweaks.sh                 # Runtime sysfs performance tweaks
│   └── pi_diagnostic.sh                     # Play Integrity & Knox diagnostics
└── tools/
    ├── a06_shield/                          # Zygisk module for Play Integrity & Knox evasion
    ├── extract_firmware.py                  # Direct LZ4 firmware decompressor (ctypes)
    ├── logo_tool.py                         # Boot logo unpacker, warning silencer & packager
    ├── repack_boot.py                       # Boot image unpacker & repacker
    └── vbmeta_tool.py                       # AVB 2.0 blank/patch utility & Odin packager
```

---

## Modules & Workflows

### 1. Boot Logo & Bootloader Warning Customization (`tools/logo_tool.py`)
Customizes the boot screen and silences the Knox "Bootloader Unlocked" orange warning screen without risking LittleKernel crashes.
```bash
# Unpack stock up_param partition
python3 tools/logo_tool.py unpack ACR-A065FXXS4AYE2-20250519143541/up_param.bin.lz4 --out boot_logo_extracted/

# Blackout bootloader unlocked warning screens (svb_orange.jpg, booting_warning.jpg)
python3 tools/logo_tool.py suppress-warning boot_logo_extracted/ --mode blackout

# Set custom logo (auto-resizes to 720x1600)
python3 tools/logo_tool.py set-logo boot_logo_extracted/ custom_logo_siaw.png

# Repack into up_param_custom.bin (for dd/root) and up_param_custom.tar (for Odin BL slot)
python3 tools/logo_tool.py repack boot_logo_extracted/ --out up_param_custom.bin
```
See [docs/boot_logo_guide.md](docs/boot_logo_guide.md) for detailed specifications.

---

### 2. APatch Root & VBMeta AVB 2.0 Bypass (`tools/vbmeta_tool.py`)
```bash
# Generate official blank disabled vbmeta (flags=0x02)
python3 tools/vbmeta_tool.py create -o vbmeta_disabled.img

# Package for Odin
python3 tools/vbmeta_tool.py pack --boot apatch_patched_*.img --vbmeta vbmeta_disabled.img -o AP_patched.tar
```

---

### 3. Custom Kernel Integration ([tools/repack_boot.py](tools/repack_boot.py))
Custom Linux `4.19.191` kernel tailored for Helio G85 on Android 14 / One UI Core 6.1 (tested & verified live on hardware):
- **SuSFS v1.5.5 Kernel Subsystem**: Native stealth hiding layer (`sus_path`, `sus_mount`, `sus_kstat`, `try_umount`, `spoof_uname`, `open_redirect`, `hide_ksu_susfs_symbols`). Communicates via standard `prctl(KERNEL_SU_OPTION)` syscall interface.
- **Integrated KernelSU-Next (Manual Hooks)**: Direct in-kernel syscall interception (`fs/exec.c`, `fs/open.c`, `fs/stat.c`, `fs/read_write.c`, `drivers/input/input.c`, `kernel/reboot.c`). Completely invisible to userspace root detection.
- **Samsung KABI & MediaTek Task Turbo Protection**: Preserved `futex_exit_mutex` across `struct task_struct` reserve slots to ensure zero scheduler panics on Helio G85.
- **Anti-Detection Identity Spoofing**: Matches authentic Samsung factory builder (`dpi@21DKGB11`) and removes the `-dirty` git flag and commit hashes from `/proc/version`.
- **Stripped Debug Symbols**: Strips DWARF debug information (`# CONFIG_DEBUG_INFO is not set`), reducing `vmlinux` size from 276 MB to 37 MB.
- **Samsung DEFEX completely removed**: No unauthorized process kills, smooth context switching.
- **LLVM LLD 17.0.2 & Compact RELR Packing**: Uncompressed kernel memory footprint reduced from 36.0MB to 30.1MB, saving ~6.0MB RAM.
- **CONFIG_KPROBES enabled**: Runtime symbol tracing for dynamic APatch KPM and `simpleperf`.
- **Default LZ4 & ZSTD compression**: Ultra-fast in-RAM zRAM swap (eliminates slow eMMC 5.1 RAM Plus freeze).
- **BBR TCP Congestion Control & FQ Pacing**: Low-latency Wi-Fi and LTE mobile networking.
- **In-Kernel WireGuard VPN**: Low-power, high-throughput encrypted tunneling.

> [!TIP]
> **Pre-compiled Binaries Ready for Download:**
> Ready-to-flash boot images (`boot_custom.img`), Odin AP packages (`AP_custom_kernel_AYE2.tar`), raw `Image` / `Image.gz`, the companion `KernelSU_Next_v3.3.0.apk`, and the `ksu_module_susfs_v1.5.5.zip` are published and verified on GitHub Releases:
> 📦 **[Download Pre-Compiled Kernel & Boot Images (Latest Release)](https://github.com/s47user/android_kernel_samsung_a06/releases/latest)**
>
> | Asset | Size | Purpose |
> | :--- | :--- | :--- |
> | `boot_custom.img` / `boot_custom_susfs.img` | 64 MB | Repacked Android boot v2 image (clean ramdisk + SEANDROIDENFORCE footer). Ready for Heimdall or `dd`. |
> | `AP_custom_kernel_AYE2.tar` / `AP_custom_kernel_susfs_AYE2.tar` | 65 MB | Odin-flashable archive containing `boot.img` and `vbmeta.img`. Flash via Odin **AP** slot. |
> | `ksu_module_susfs_v1.5.5.zip` | 185 KB | Companion SuSFS v1.5.5 module for KernelSU Next Manager. |
> | `Image.gz` / `Image` | 12.5 MB / 30 MB | Gzip-compressed / raw AArch64 kernel binaries. |
> | `KernelSU_Next_v3.3.0.apk` | 9.8 MB | Companion KernelSU Next Manager application. |
> | `sha256sums.txt` | Text | SHA-256 integrity checksums. |

#### Flashing to Device

##### Method A: Direct Shell Flashing (Rooted)
```bash
adb push boot_custom.img /data/local/tmp/
adb shell "su -c 'dd if=/data/local/tmp/boot_custom.img of=/dev/block/by-name/boot bs=4096 && sync && reboot'"
```

##### Method B: Heimdall (Direct Linux Flashing)
Put the phone into Download Mode (`adb reboot download`) and execute in a clean single session:
```bash
heimdall flash --pit a06.pit --boot boot_custom.img
```

##### Method C: Odin / Odin4 (AP Slot)
Flash the repacked tar package containing `boot.img` and `vbmeta.img`:
```bash
./odin4 -a AP_custom_kernel_AYE2.tar
```

---

### 4. Play Integrity & Knox Shield ([tools/a06_shield/](tools/a06_shield/))
Custom Zygisk module designed to spoof device properties, bypass Knox flags, and pass Play Integrity (BASIC + DEVICE integrity).

---

### 5. Performance & System Tweaks ([scripts/apply_safe_tweaks.sh](scripts/apply_safe_tweaks.sh))
- **RAM Plus**: Must be disabled (`Settings -> Device Care -> Memory -> RAM Plus -> OFF`) to eliminate eMMC wear and micro-stutters.
- **zRAM**: 2GB zRAM configured using LZ4 compression at 70 swappiness.
- **Schedutil**: Big-core rate limit tuned to 500µs for instantaneous touch responsiveness.

---

### 6. Custom Stock-Based ROM v1.6 — Master Polish Generation ([modules/a06_experience_suite/](modules/a06_experience_suite/))
A production-grade, debloated custom ROM and companion systemless suite for the **Samsung Galaxy A06 (`SM-A065F`)** running Android 14 / One UI Core 6.1 (`A065FXXS4AYE2`). v1.6 introduces the **Master Polish Generation** — deep system surgery targeting latency, battery, and daily-driver polish on top of the Realist Silicon Engine from v1.5.

#### Master Polish Architecture (v1.6 — New):
* **Native Fingerprint AppLock** (no Knox required): CSC injection of `CscFeature_SmartManager_ConfigSubFeatures=AppLock` and `CscFeature_Common_SupportAppLock=TRUE` exposes the native Samsung biometric app-locking UI inside Device Care.
* **SQLite WAL Zero-Stutter**: `debug.sqlite.wal=1` and `persist.sys.sqlite.sync=NORMAL` replace the default synchronous `fsync()` after each database commit with write-ahead logging, eliminating micro-stutters during app scrolling and notification processing.
* **HWC 100% Pass-Through**: `debug.sf.enable_hwc_vds=1` and `ro.surface_flinger.max_frame_buffer_acquired_buffers=3` disable SurfaceFlinger software compositing fallback, keeping all composition on the Mali-G52 hardware path.
* **HWUI Pre-Render Pipeline**: `debug.hwui.render_ahead=2` pipelines two frames ahead to hide GPU command submission latency at 60 Hz.
* **2.5s Cellular Fast Dormancy**: CSC injection of `CscFeature_RIL_FastDormancyWaitTimer=2.5` releases high-power LTE radio channels 2.5s after push notifications, reducing idle radio tail energy — critical in fringe signal zones.
* **Digital Wellbeing Daemon Freeze**: `com.samsung.android.forest` and `com.google.android.apps.wellbeing` background daemons are frozen at boot, eliminating the 100–150ms app-switch hitch from usage-stats I/O. User can unfreeze from Settings anytime.
* **McAfee Scanner Purge (~80MB PSS)**: `com.samsung.android.sm.devicesecurity` is disabled at boot, reclaiming ~80MB resident RAM. User can re-enable anytime.
* **SoundAlive Adapt Sound**: Floating feature `SEC_FLOATING_FEATURE_AUDIO_SUPPORT_ADAPT_SOUND=TRUE` unlocks the personalized hearing profile calibration tool in Samsung Sound settings.
* **MiraVision LCD CABC**: Service script probes MediaTek dispsys1 and fb0 sysfs nodes for Content-Adaptive Backlight Control mode 1 (UI mode), reducing LCD backlight current by 15–20%.
* **SmartSwitch Post-Setup Cleanup**: Dormant `com.sec.android.easyMover.Agent` background receivers are deactivated after initial device setup.

#### Realist Optimization Architecture (v1.5 — Retained):
* **CPUSET Big-Core Gating**: Confines background daemons (`/dev/cpuset/background`, `system-background`, `restricted`) strictly to Cortex-A55 Little cores (0–3), ensuring the two Cortex-A75 Big cores remain completely dormant during screen-off and 100% responsive during UI interactions.
* **Storage Writeback Batching**: Batches dirty VM pages every 15 seconds (`vm.dirty_writeback_centisecs = 1500`) instead of 5s, reducing eMMC 5.1 NAND controller wakeups and standby power consumption.
* **eMMC 5.1 Bus Optimization**: Enforces `mq-deadline` scheduler, 128KB read-ahead buffer, and `rq_affinity = 2` to prevent UI frame drops on half-duplex flash memory during background writes.
* **15-Second Quick Doze**: Injects accelerated light-idle parameters into `device_idle_constants`, entering deep sleep 15s after screen-off while retaining instant high-priority FCM notifications (WhatsApp, Telegram, Calls).
* **Hardware Battery Protection**: Pre-configures native One UI battery protection mode (80% lifespan cap) to preserve lithium-ion cells from high-voltage degradation.
* **ART AOT Pre-Compiler (`scripts/a06_art_optimizer.sh`)**: Direct tool to compile app bytecode to native ARM64 machine code via Google Play cloud profiles, eliminating JIT compilation stutter.
* **UI Fluidity**: Scales window, transition, and animator durations to `0.75x` for responsive 60Hz/90Hz panel performance.

#### Verified Working Feature Matrix:
| Feature | Scope | Implementation Mechanism | Live Verification |
| :--- | :--- | :--- | :--- |
| **Real-Time Network Speed** | Status Bar & Settings | Injected CSC Feature (`CscFeature_Setting_SupportRealTimeNetworkSpeed`) + Global OMC flag | Live upload/download rate dynamically rendered in status bar. |
| **Native 2-Way Call Recording** | InCallUI & Phone App | CSC Feature (`CscFeature_VoiceCall_ConfigRecording=RecordingAllowed`) | In-call recording button & auto-record menu active in Samsung Phone settings. |
| **Camera Shutter Sound Toggle** | Samsung Camera | ODM project override (`ro.vendor.cam.name=M1`) | Dedicated "Shutter sound" ON/OFF switch in Camera Settings. |
| **Full Samsung Screen Recorder** | SmartCapture & SystemUI | Floating feature flag + QS Tile + overlay permission | 1080p high quality recording, PIP selfie video slider, Quick Settings tile. |
| **System-Wide Dolby Atmos** | SoundAlive & Audio HAL | Floating feature (`AUDIO_SUPPORT_DOLBY_AUDIO`, stereo SoundAlive profiles) | Dolby Atmos tile in Quick Settings and custom equalizer presets. |
| **Smart Call & Spam Protection** | Samsung Contacts & Phone | Hiya anti-malware provider CSC flag (`CscFeature_VoiceCall_SupportCallProtect`) | Caller ID & spam call identification. |
| **Separate App Sound** | AudioService (MultiSound) | Floating feature (`AUDIO_SUPPORT_SEPARATE_APP_SOUND`) | Independent audio routing per application. |
| **High-End UI & Blur Effects** | Launcher & SurfaceFlinger | Floating feature (`LAUNCHER_CONFIG_ANIMATION_TYPE=HighEnd`) | Fluid animations and partial blur. |
| **Native Fingerprint AppLock** | Device Care / SmartManager | CSC Features (`CscFeature_SmartManager_ConfigSubFeatures=AppLock`, `CscFeature_Common_SupportAppLock=TRUE`) | Biometric app lock menu visible in Device Care without Knox. |
| **SoundAlive Adapt Sound** | Samsung Sound Settings | Floating feature (`SEC_FLOATING_FEATURE_AUDIO_SUPPORT_ADAPT_SOUND=TRUE`) | Personalized hearing profile calibration tool unlocked. |
| **2.5s Cellular Fast Dormancy** | Modem / RIL | CSC Features (`CscFeature_RIL_FastDormancyWaitTimer=2.5`, `CscFeature_RIL_SupportFastDormancy=TRUE`) | Reduced LTE radio tail power in fringe signal zones. |

#### Installation & Flashing (v1.6):
- **Odin SUPER_ONLY Package**: [`AP_A065F_Debloated_V1.6_SUPER_ONLY.tar.md5`](AP_A065F_Debloated_V1.6_SUPER_ONLY.tar.md5) (`8047f87ff025905d970330bd5fd1cb2c7627f0718ad471ce4260f90214a6250d`)
- **Full Odin AP Package**: [`AP_A065F_Debloated_V1.6.tar.md5`](AP_A065F_Debloated_V1.6.tar.md5) (`0a3f638141c27accd0b597a94ba1a6c5448b37ce94253af8641fa3960f5a64e3`)
- **Standalone Module**: [`modules/a06_experience_suite.zip`](modules/a06_experience_suite.zip) (`v3.2-Master`, `262 KB`, `dc532918be14a68056fa71e23b9281342e2a9b5fb4cc64b29f61450890c756d1`)
- **Diagnostic Scripts**: [`scripts/a06_battery_optimizer.sh`](scripts/a06_battery_optimizer.sh) and [`scripts/a06_art_optimizer.sh`](scripts/a06_art_optimizer.sh)

---

## References & Credits

Special thanks and sincere credit to the developers, projects, and communities that made this toolkit and custom kernel possible:

- **Samsung Open Source Release Center (OSRC)** for releasing stock device kernel source code (`SM-A065F_14_Opensource_A065FXXS4AYE2`).
- **tiann & The KernelSU Team** for KernelSU architecture and kernel-space su authorization.
- **rifsxd & pershoot (KernelSU-Next Team)** for KernelSU-Next legacy architecture, non-GKI backports, and manual hooking implementations.
- **physwizz** for foundational MediaTek Helio G85 custom kernel research and optimization methodology.
- **topjohnwu & The Magisk Team** for Magisk root and `magiskboot` ramdisk live-patching under `Enforcing` SELinux.
- **bmax121 & The APatch Team** for APatch and KernelPatch dynamic symbol hooking.
- **Jason A. Donenfeld & The WireGuard Project** for the in-kernel WireGuard VPN implementation.
- **Google Linux / AOSP Team** for Clang toolchain support, BBR TCP congestion control, and Fair Queuing packet schedulers.
- **Benjamin Dobell / Glass Echidna** for Heimdall Suite.
- **Llucs / Samsung Electronics** for Odin4 Linux CLI utilities.
- **Willi Ye (Grarak) & The SmartPack Team** for Kernel Adiutor and SmartPack Kernel Manager.
