# Samsung Galaxy A06 (SM-A065F) Master Development Toolkit

Unified engineering toolkit, custom kernel research, boot logo customization, and rooting procedures for the **Samsung Galaxy A06 (`SM-A065F`)** running **Android 14 / One UI Core 6.1 (MediaTek Helio G85 MT6769V)**.

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

### 3. Custom Kernel Flashing (`tools/repack_boot.py`)
Custom Linux `4.19.191` kernel tailored for Helio G85:
- **Samsung DEFEX completely removed** (no unauthorized process kills).
- **CONFIG_KPROBES enabled** (full support for dynamic APatch KernelPatch Modules / KPM).
- **LZ4 & ZSTD compression** for high-speed in-RAM zRAM swap.
- **BBR TCP Congestion Control** enabled for low-latency networking.

---

### 4. Play Integrity & Knox Shield (`tools/a06_shield/`)
Custom Zygisk module designed to spoof device properties, bypass Knox flags, and pass Play Integrity (BASIC + DEVICE integrity).

---

### 5. Performance & System Tweaks (`scripts/apply_safe_tweaks.sh`)
- **RAM Plus**: Must be disabled (`Settings -> Device Care -> Memory -> RAM Plus -> OFF`) to eliminate eMMC wear and micro-stutters.
- **zRAM**: 2GB zRAM configured using LZ4 compression at 70 swappiness.
- **Schedutil**: Big-core rate limit tuned to 500µs for instantaneous touch responsiveness.

---

## References & Credits
- **APatch / KernelPatch**: [bmax121/APatch](https://github.com/bmax121/APatch)
- **Heimdall Suite**: [Benjamin Dobell / Glass Echidna](https://glassechidna.com.au/heimdall/)
- **Odin4 for Linux**: Samsung Electronics Co., Ltd. / [Llucs/odin4](https://github.com/Llucs/odin4)
- **Custom Kernel Research**: Developer **physwizz** (MediaTek Helio G85 kernel ecosystem)
