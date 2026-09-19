# TWRP & OrangeFox Recovery Device Tree for Samsung Galaxy A06 (`SM-A065F`)

Unified device tree for building **TWRP (Team Win Recovery Project)** and **OrangeFox Recovery Project (OFRP)** for the **Samsung Galaxy A06 (`SM-A065F` / `SM-A065M`)** on **MediaTek Helio G85 (`MT6769V/CZ`)**.

---

## Device Specifications

| Specification | Value |
| :--- | :--- |
| **SoC** | MediaTek Helio G85 (`MT6769V/CZ`) |
| **CPU** | 2x Cortex-A75 @ 2.0 GHz + 6x Cortex-A55 @ 1.8 GHz |
| **GPU** | ARM Mali-G52 2EEMC2 |
| **Architecture** | 64-bit ARM (`arm64-v8a`) |
| **Kernel Version** | `4.19.191` (Non-GKI, Android Boot Header v2) |
| **Display** | 720 × 1600 (20:9 Aspect Ratio) |
| **Touchscreen** | Himax HX83108 / GalaxyCore GC7272 / FocalTech FT8057P |
| **Storage** | eMMC 5.1 |
| **Dynamic Partitions** | EROFS inside `super.img` (Group: `main`, 9.64 GB) |
| **Recovery Partition** | Dedicated physical partition (`89,128,960` bytes / 85.0 MB) |
| **Boot Partition** | Dedicated physical partition (`67,108,864` bytes / 64.0 MB) |
| **Firmware Base** | `A065FXXS4AYE2` (Android 14 / One UI Core 6.1) |

---

## Directory Structure

```text
device/samsung/a06/
├── Android.mk
├── AndroidProducts.mk
├── omni_a06.mk
├── twrp_a06.mk
├── BoardConfig.mk
├── device.mk
├── vendorsetup.sh
├── recovery.fstab
├── prebuilt/
│   ├── kernel               # Authentic 4.19.191 Samsung stock recovery kernel (Image.gz)
│   ├── dtb.img              # Compiled DTB table (v2 boot header compatible)
│   └── single_dtb.dtb       # Extracted single device tree binary
└── recovery/
    └── root/
        ├── init.recovery.mt6768.rc
        ├── init.recovery.samsung.rc
        └── system/etc/
            ├── recovery.fstab
            └── twrp.flags
```

---

## How to Build

### Option A: Building with Minimal TWRP Manifest (Android 12.1 / 11)

1. **Initialize the TWRP Build Environment**:
   ```bash
   mkdir twrp && cd twrp
   repo init -u https://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp.git -b twrp-12.1
   repo sync -j$(nproc --all) --current-branch --no-tags --no-clone-bundle
   ```

2. **Clone this Device Tree**:
   ```bash
   mkdir -p device/samsung/a06
   cp -r /path/to/ROM\ AND\ CUSTOM\ OS\ PORTING/device/samsung/a06/* device/samsung/a06/
   ```

3. **Build the Recovery Image**:
   ```bash
   source build/envsetup.sh
   lunch twrp_a06-eng || lunch omni_a06-eng
   mka recoveryimage -j$(nproc --all)
   ```

---

### Option B: Building with OrangeFox Recovery Project (OFRP)

1. **Initialize OrangeFox Manifest**:
   ```bash
   mkdir fox_12.1 && cd fox_12.1
   repo init -u https://gitlab.com/OrangeFox/manifest.git -b fox_12.1
   repo sync -j$(nproc --all) --current-branch --no-tags --no-clone-bundle
   ```

2. **Copy Device Tree**:
   ```bash
   mkdir -p device/samsung/a06
   cp -r /path/to/ROM\ AND\ CUSTOM\ OS\ PORTING/device/samsung/a06/* device/samsung/a06/
   ```

3. **Build**:
   ```bash
   source build/envsetup.sh
   lunch omni_a06-eng
   mka recoveryimage -j$(nproc --all)
   ```

---

## Flashing & Installation Guide

1. **Append Samsung `SEANDROIDENFORCE` Signature**:
   ```bash
   echo -n "SEANDROIDENFORCE" >> recovery.img
   ```

2. **Package into Odin Flashable Archive (`.tar`)**:
   ```bash
   tar -H ustar -c recovery.img > recovery.tar
   md5sum -t recovery.tar >> recovery.tar
   mv recovery.tar recovery.tar.md5
   ```

3. **Flash via Odin4 (Linux CLI)**:
   ```bash
   sudo ./odin4 -b recovery.tar.md5
   # Or flash raw partition with Heimdall:
   heimdall flash --recovery recovery.img --no-reboot
   ```

> [!IMPORTANT]
> - Always keep **`vbmeta_disabled.img`** flashed to the `vbmeta` partition to disable Samsung Verified Boot checks.
> - Samsung's hardware-backed Knox TEE prevents on-the-fly decryption of stock encrypted `/data` partitions. Keep flashable zips on an external MicroSD card or USB-OTG drive.
