# APatch Root Guide for Samsung Galaxy A06 (SM-A065F)

## Target Specifications
- **Model**: Samsung Galaxy A06 (`SM-A065F`)
- **Chipset**: MediaTek Helio G85 (`MT6769V`)
- **Firmware Base**: `A065FXXS4AYE2` (Android 14 / One UI Core 6.1)
- **Kernel Version**: `4.19.191` (Non-GKI architecture, ramdisk inside `boot.img`)

---

## 1. Prerequisites
1. **Bootloader Unlocked**:
   - `OEM LOCK: OFF` verified on the Download Mode screen.
   - Note: Bootloader unlock trips Knox to `0x1` permanently.
2. **Stock Firmware**:
   - Download matching firmware (`A065FXXS4AYE2`) from Samsung FUS or SamFW.
   - Extract `boot.img.lz4` and `vbmeta.img.lz4` from the `AP_*.tar.md5` package.

---

## 2. Decompression
Samsung packs partition binaries inside LZ4 frames. Decompress to raw images:
```bash
python3 tools/extract_firmware.py path/to/boot.img.lz4 boot.img
python3 tools/extract_firmware.py path/to/vbmeta.img.lz4 vbmeta.img
```

---

## 3. Patching with APatch
1. Transfer raw `boot.img` (67,108,864 bytes) to your phone's `Download/` folder.
2. Install the latest **APatch Manager APK** on your phone.
3. Tap **Patch** -> **Select a file to patch** -> Select `boot.img`.
4. Enter your chosen **SuperKey** (8–64 character passphrase).
5. **KPM Note**: Leave KPM (KernelPatch Modules) disabled on the stock kernel. Standard userspace APM modules (Zygisk Next, Shamiko, PlayIntegrityFix) do not require KPM.
6. Tap **Start**.
7. Copy the generated `apatch_patched_*.img` back to your computer.

---

## 4. VBMeta Handling (AVB 2.0 Bypass)
Samsung's Little Kernel (LK) verifies partition integrity via `vbmeta.img`. Because the patched kernel has a different cryptographic hash, stock vbmeta will halt boot with `VBMETA: Error verifying...`.

Generate the official 4,096-byte disabled vbmeta:
```bash
python3 tools/vbmeta_tool.py create -o vbmeta_disabled.img --flags 2
```

---

## 5. Flashing Methods (Linux)

### Method A: Heimdall CLI (Recommended on Linux)
1. Turn off phone.
2. Hold **Vol Up + Vol Down** and plug into PC.
3. Press **Vol Up once** at the teal warning screen to enter Download Mode.
4. Flash using the partition table map:
   ```bash
   sudo heimdall flash --pit a06.pit --boot apatch_patched_*.img --vbmeta vbmeta_disabled.img --no-reboot
   ```

### Method B: Samsung Odin4 CLI (Linux) / Odin v3 (Windows)
1. Build the tar package:
   ```bash
   python3 tools/vbmeta_tool.py pack --boot apatch_patched_*.img --vbmeta vbmeta_disabled.img -o AP_patched.tar
   ```
2. Flash in Linux via `odin4`:
   ```bash
   sudo ./odin4 -a AP_patched.tar
   ```
3. Or in Windows: place `AP_patched.tar` into the **AP** slot in Odin v3.14.4 and click **Start**.

---

## 6. Mandatory Post-Flash Data Wipe (FBE Reset)
> **WARNING**: When booting an unverified boot image for the first time, Android's File-Based Encryption (FBE) invalidates master Keystore keys. A factory reset is mandatory.

1. As soon as flashing reaches 100% and screen shuts off, immediately hold **Power + Volume Up**.
2. When the Samsung Galaxy logo appears, release Power and hold Volume Up until **Android Recovery** appears.
3. Select **Wipe data / factory reset** -> Confirm.
4. Select **Reboot system now**.
5. Wait 3–5 minutes for initial setup, then launch APatch, enter your SuperKey, and confirm root access!
