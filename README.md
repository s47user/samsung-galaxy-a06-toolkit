# Samsung Galaxy A06 (SM-A065F) Development Toolkit

Engineering toolkit, rooting procedures, partition tools, and custom kernel research for the **Samsung Galaxy A06 (`SM-A065F`)** running **Android 14 / One UI Core 6.1 (Helio G85 MT6769V)**.

---

## Device Profile
| Specification | Value |
| :--- | :--- |
| **Model** | Samsung Galaxy A06 (`SM-A065F`) |
| **SoC** | MediaTek Helio G85 (`MT6769V/CZ`) |
| **CPU** | 2x Cortex-A75 @ 2.0 GHz + 6x Cortex-A55 @ 1.8 GHz |
| **GPU** | ARM Mali-G52 2EEMC2 |
| **Storage** | eMMC 5.1 |
| **Filesystem** | EROFS (Dynamic Partitions inside `super.img`) |
| **Baseband** | `A065FXXS4AYE1` / Build `A065FXXS4AYE2` |
| **Kernel Version** | `4.19.191` (Non-GKI architecture, ramdisk in `boot.img`) |
| **Verified Boot** | AVB 2.0 (`vbmeta.img`) |

---

## Repository Structure
```text
├── README.md                                # Master documentation
├── .gitignore                               # Binary & firmware exclusion rules
├── configs/
│   └── physwizz_kernel_optimizations.config # Defconfig optimization matrix
├── docs/
│   ├── apatch_root_guide.md                 # Complete APatch flashing guide
│   ├── custom_kernel_guide.md               # Kernel compilation & Physwizz methodology
│   └── performance_tuning.md                # eMMC bottleneck fixes & sysfs tuning
└── tools/
    ├── vbmeta_tool.py                       # AVB 2.0 blank/patch utility & Odin packager
    └── extract_firmware.py                  # Direct LZ4 firmware decompressor (ctypes)
```

---

## Quick Start: APatch Root & VBMeta Bypass

### 1. Generate / Patch VBMeta
```bash
# Generate official blank disabled vbmeta (flags=0x02)
python3 tools/vbmeta_tool.py create -o vbmeta_disabled.img

# Or patch flags directly in stock vbmeta
python3 tools/vbmeta_tool.py patch vbmeta.img -o vbmeta_patched.img
```

### 2. Package for Odin
```bash
python3 tools/vbmeta_tool.py pack --boot apatch_patched_*.img --vbmeta vbmeta_disabled.img -o AP_patched.tar
```

### 3. Flash on Linux via Heimdall
```bash
sudo heimdall flash --pit a06.pit --boot apatch_patched_*.img --vbmeta vbmeta_disabled.img --no-reboot
```

> **IMPORTANT**: A factory reset via **Stock Recovery** (`Wipe data / factory reset`) is mandatory immediately following the first flash due to Android 14 File-Based Encryption (FBE) key invalidation.
> Subsequent flashes of boot/kernel packages will **NOT** wipe your data.

---

## Custom Kernel Flashing (`AP_custom_kernel_AYE2.tar`)

The custom kernel (Linux `4.19.191`) integrates:
- **Samsung DEFEX completely stripped** (no unauthorized process kills).
- **CONFIG_KPROBES enabled** (full support for dynamic APatch KernelPatch Modules / KPM).
- **LZ4 & ZSTD compression** compiled in for high-speed in-RAM zRAM.
- **Google BBR TCP congestion control** enabled.
- **In-kernel WireGuard** enabled.

### Flash via Odin (Windows / Linux)
```bash
# In Linux via odin4:
sudo ./odin4 -a AP_custom_kernel_AYE2.tar

# Or in Windows: place AP_custom_kernel_AYE2.tar into AP slot in Odin v3.14.4
```

## Performance & Optimization Notes
- **Eliminate eMMC Stutter**: Disable Samsung **RAM Plus** immediately (`Settings -> Device Care -> Memory -> RAM Plus -> OFF`).
- **In-RAM zRAM**: Configure 2GB zRAM using LZ4 compression at 100 swappiness via **SmartPack Kernel Manager**.
- **CPU Scheduling**: Tune Schedutil big-core rate limit to 500µs for instant touch response.

---

## References & Credits
- **APatch / KernelPatch**: [bmax121/APatch](https://github.com/bmax121/APatch)
- **Heimdall Suite**: [Benjamin Dobell / Glass Echidna](https://glassechidna.com.au/heimdall/)
- **Odin4 for Linux**: Samsung Electronics Co., Ltd. / [Llucs/odin4](https://github.com/Llucs/odin4)
- **Custom Kernel Research**: Developer **physwizz** (MediaTek Helio G85 kernel ecosystem)
