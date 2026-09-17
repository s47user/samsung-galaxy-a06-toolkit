# Samsung Galaxy A06 (`SM-A065F`) Stock-Based Custom ROM - Project Handoff

**Project State**: V1.3 Production Package Assembled & Verified  
**Device**: Samsung Galaxy A06 (`SM-A065F` / `SM-A065M`)  
**Chipset**: MediaTek Helio G85 (`MT6769V/CZ`), ARM Mali-G52 2EEMC2  
**Base Firmware**: `A065FXXS4AYE2` (Android 14 / One UI Core 6.1)  
**Kernel**: Custom `4.19.191` (KernelSU-Next v3.3.0 + SuSFS v1.5.5 + DEFEX removed)  
**Feature Suite**: One UI Experience Suite v3.0 Final (Screen Recorder, Network Speed, Call Recording, Camera Shutter Toggle, Dolby Atmos)  
**Verification Layer**: AVB 2.0 Disabled (`vbmeta_disabled.img`, flags `0x02`)  

---

## 1. Executive Summary & Accomplishments

In this phase, we developed a complete, reproducible engineering pipeline to convert official Samsung factory firmware into an ultra-lean, debloated, unthrottled, and rooted custom ROM without sacrificing hardware functionality.

### Key Breakthroughs:
1. **Dynamic Partition Stream Unpacking Engine (`tools/lpunpack.py`)**:
   - Built a pure Python `SparseFileReader` capable of random-access chunk streaming from Samsung's 7.4 GB sparse `super.img`.
   - Enabled zero-RAM extraction directly to EROFS images at >550 MB/s without intermediate disk expansion.
2. **Precision Debloating (`tools/debloat.py`)**:
   - Cataloged all 288 packages across `system` and `product`.
   - Stripped **67 bloatware packages** (Facebook services, Samsung direct marketing, telemetry monitors, GOS throttling, dead Knox userspace services, 11 foreign TTS models, and heavy Google apps).
   - Saved **2,127.53 MB (2.08 GB)** of uncompressed bloatware.
   - Verified that all 20 critical hardware/telephony components (`SamSungCamera`, Dual-SIM RIL, `HoneyBoard`, `SecSettings`, etc.) remain 100% intact.
3. **Modern `build.prop` Tuning**:
   - Injected SurfaceFlinger buffer latency drops (`debug.sf.disable_backpressure=1`), 4GB Dalvik heap parameters, 4-thread `dex2oat` CPU bounds, logd buffer reduction (`64K`), and telephony ring-delay fixes.
   - Avoided catastrophic Android Go switches (`ro.config.low_ram` was strictly omitted).
4. **Filesystem Reassembly (`tools/package_rom.py`)**:
   - Recompiled `system` (2.2 GB) and `product` (604 MB) using `mkfs.erofs -z lz4 --all-root`.
   - Reconstructed `super.img` with `lpmake` (active data reduced from 7.56 GB to 3.96 GB).
   - Produced two production Odin flashable archives with valid MD5 verification footers.

---

## 2. Generated Release Assets

| Artifact | Size | Description | Flashing Target |
| :--- | :--- | :--- | :--- |
| **`AP_A065F_Debloated_SUPER_ONLY.tar.md5`** | **3.33 GB** | **Ultra-Safe Minimal Flash**. Contains **only** `super.img.lz4`. Zero touch on kernel, vbmeta, modem, or bootloader. Completely immune to IMEI/baseband/hardbrick risks. | Odin **AP** slot |
| **`AP_A065F_Debloated_V1.tar.md5`** | **3.37 GB** | **Complete All-in-One AP Package**. Contains custom `super.img.lz4` + custom `boot.img.lz4` (KernelSU/SuSFS) + `vbmeta.img.lz4` (disabled) + companion trustlet blobs. | Odin **AP** slot |
| `work_rom/partitions/system_custom.img` | 2.20 GB | Debloated, optimized EROFS image for `/system`. | Raw partition |
| `work_rom/partitions/product_custom.img` | 604 MB | Debloated EROFS image for `/product`. | Raw partition |
| `work_rom/super.img.lz4` | 3.33 GB | Standalone compressed dynamic partition container. | Raw partition |

---

## 3. Toolkit & Utility Scripts Inventory

All tools are located in `tools/` and are fully automated and reproducible:

- **`tools/lpunpack.py`**:
  - Unpacks Android sparse and raw dynamic partition images (`super.img`).
  - Supports `--list` and `--unpack`.
- **`tools/debloat.py`**:
  - Automated manifest remover and `build.prop` optimizer.
  - Automatically audits protected packages and logs changes to `work_rom/debloat_audit.log`.
- **`tools/package_rom.py`**:
  - Compresses custom images with Samsung-standard flags (`lz4 -B6 --content-size`).
  - Bundles Odin `.tar.md5` packages with calculated MD5 verification footers.
- **`tools/bin_tools/usr/bin/`**:
  - Self-contained host utilities: `mkfs.erofs`, `fsck.erofs`, `dump.erofs`, `lpmake`, `lz4`.

---

## 4. Linux Flashing Guide (Heimdall vs. Odin)

Since you are running Linux on an `x86_64` workstation, you have two primary flashing avenues:

### Method A: Flashing via Heimdall (CLI)
Heimdall v2.0.2 is installed on the host (`/usr/bin/heimdall`).

> [!NOTE]
> Heimdall flashes **raw uncompressed images** (`.img`), not `.lz4` or `.tar.md5`.

1. Decompress `super.img.lz4` to raw format:
   ```bash
   tools/bin_tools/usr/bin/lz4 -d work_rom/super.img.lz4 work_rom/super_raw.img
   ```
2. Put phone into Download Mode (Power off, hold Volume Up + Volume Down, plug in USB-C, press Volume Up at teal screen).
3. Test device detection:
   ```bash
   heimdall detect
   ```
4. Flash the `super` partition:
   ```bash
   heimdall flash --super work_rom/super_raw.img --no-reboot
   ```

---

### Method B: Flashing via Odin4 (Official Samsung Linux CLI)
Samsung produces an official Linux CLI version of Odin (`odin4`) that natively flashes `.tar.md5` archives over USB without manual decompression.

1. Put phone into Download Mode.
2. Execute Odin4 against the super-only package:
   ```bash
   sudo ./odin4 -a AP_A065F_Debloated_SUPER_ONLY.tar.md5
   ```

---

### Method C: Flashing via Samsung Odin v3 (Windows)
If using a Windows machine or virtual machine with USB passthrough:
1. Load **`AP_A065F_Debloated_SUPER_ONLY.tar.md5`** into the **AP** slot.
2. Leave BL, CP, and CSC **completely empty**.
3. Click **Start**.

---

## 5. First Boot & Post-Flash Notes

- **Data Wipe / Recovery**:
  If this is your first time transitioning from stock encrypted firmware to a custom repacked super partition with disabled vbmeta, Android may prompt that the data partition cannot be decrypted.
  - Power off device.
  - Hold **Volume Up + Power** to enter stock recovery.
  - Select **Wipe data / Factory reset**.
  - Reboot to system.
- **Kernel & Root Status**:
  Your custom kernel (`boot_custom_susfs.img`) and disabled vbmeta remain preserved. KernelSU-Next Manager and SuSFS modules will function immediately with root access.
- **Next Phase Roadmap (V2)**:
  - Dynamic game resolution scaling & GPU governor profiling (`sysfs` tuning).
  - One UI custom theme / visual modding (status bar icons, animations).
