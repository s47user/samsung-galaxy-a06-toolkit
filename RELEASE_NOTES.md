# Samsung Galaxy A06 (`SM-A065F`) Custom Kernel v1.0.0
### Production Release with KernelSU-Next, Build Identity Spoofing & Physwizz Optimizations

An optimized custom Linux 4.19.191 kernel for **Samsung Galaxy A06 (`SM-A065F` / `SM-A065M`)** running **Android 14 (One UI Core 6.1 / AYE2 firmware)** on the **MediaTek Helio G85 (MT6769V)** chipset. Tested and verified live on physical hardware.

---

## 🚀 Key Highlights & Features

- **Integrated KernelSU-Next (v3.3.0 / 33214)**:
  - Full manual source hooks (`fs/exec.c`, `fs/open.c`, `fs/stat.c`, `fs/read_write.c`, `drivers/input/input.c`, `kernel/reboot.c`).
  - Kernel-level su domain authorization, completely invisible to userspace root detectors.
  - Packaged with clean, unpatched factory stock Samsung ramdisk (zero Magisk conflicts).
- **Anti-Detection Build Spoofing**:
  - Builder spoofed to authentic factory string: `dpi@21DKGB11`.
  - Zero `-dirty` git tags and zero custom commit hashes in `/proc/version`.
  - Exact stock version: `4.19.191-29401052-abA065FXXS4AYE2`.
- **Stripped DWARF Debug Info (`CONFIG_DEBUG_INFO`)**:
  - Reduced `vmlinux` memory footprint from **276 MB down to 37 MB**.
- **Stripped Samsung DEFEX Anti-Tamper**:
  - Completely eliminates Samsung's kernel-level process killer (`fs/exec.c`) for smooth context switching.
- **Compact LLD 17 Linking & RELR Relocation Packing**:
  - Built with LLVM Clang 17.0.2 + LLD 17.0.2 with experimental relative relocation packing.
  - Uncompressed kernel image reduced from 36.0 MB to 30.1 MB (saving ~6 MB physical RAM).
- **Fast In-RAM zRAM (Defaulting to LZ4)**:
  - Bypasses slow eMMC 5.1 RAM Plus disk-swap stutter.
- **Google BBR TCP Congestion Control & FQ Pacing**:
  - Low-latency, high-throughput Wi-Fi and mobile LTE data.
- **In-Kernel WireGuard VPN**:
  - Hardware-efficient cryptographic VPN tunneling in kernel space.

---

## 📦 Release Assets & Checksums

| File | Size | Description |
| :--- | :--- | :--- |
| `boot_custom.img` | 64 MB | Repacked Android boot v2 image (clean ramdisk + SEANDROIDENFORCE footer). Ready for Heimdall or `dd`. |
| `AP_custom_kernel_AYE2.tar` | 65 MB | Odin-flashable archive containing `boot.img` and `vbmeta.img`. Flash via Odin **AP** slot. |
| `Image.gz` | 12 MB | Gzip-compressed kernel binary for AnyKernel3 or custom repacking. |
| `Image` | 30 MB | Raw uncompressed AArch64 kernel binary. |
| `KernelSU_Next_v3.3.0.apk` | 9.8 MB | Companion KernelSU Next Manager application. |
| `sha256sums.txt` | Text | SHA-256 integrity checksums. |

### SHA-256 Checksums
```text
3efae099e655cc66a917a0c29612066f0e7ee03e09c42238cf212d92fcc34594  Image
ccb8eb3ba81e6c388605f965c4f6e2e08eff0ef40e24db9bee53b6dd90cc7b65  Image.gz
58b9d41997af90e8a8cc944629615823fae2c94d6df8c453bebe88688c72aa08  boot_custom.img
0bb0b528457f580cff8716a83ee7d69fb6aba633807249e73f357773cf13bf01  AP_custom_kernel_AYE2.tar
fd0b12385c98fe9d5f4f1257b5f184e55c74c1376637507df0718305f5d7a924  KernelSU_Next_v3.3.0.apk
```

---

## 🛠️ Flashing Guide

### Method 1: Heimdall (Linux CLI)
Reboot phone into Download Mode:
```bash
adb reboot download
heimdall flash --pit a06.pit --boot boot_custom.img
```

### Method 2: Odin (Windows PC)
1. Reboot phone into Download Mode.
2. Select `AP_custom_kernel_AYE2.tar` in the **AP** slot.
3. Click **Start**.

### Method 3: Direct Shell (If Already Rooted)
```bash
adb push boot_custom.img /sdcard/
adb shell su -c "dd if=/sdcard/boot_custom.img of=/dev/block/by-name/boot bs=4096 conv=fsync"
adb reboot
```

---

## ❤️ Credits & Acknowledgements
- **Samsung Open Source Release Center (OSRC)** for stock source code (`A065FXXS4AYE2`).
- **tiann** (KernelSU author) & **rifsxd / pershoot** (KernelSU-Next team).
- **physwizz** for Helio G85 kernel research & governor optimizations.
- **topjohnwu & The Magisk Team**.
- **bmax121 & The APatch Team**.
