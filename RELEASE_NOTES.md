# Samsung Galaxy A06 (`SM-A065F`) Custom Kernel v1.1.0
### Production Release with SuSFS v1.5.5, KernelSU-Next v3.3.0 & Anti-Detection Architecture

An optimized custom Linux 4.19.191 kernel for **Samsung Galaxy A06 (`SM-A065F` / `SM-A065M`)** running **Android 14 (One UI Core 6.1 / AYE2 firmware)** on the **MediaTek Helio G85 (MT6769V)** chipset. Tested and verified live on physical hardware.

---

## 🚀 Key Highlights & Features

- **SuSFS v1.5.5 Kernel Subsystem Integration (`CONFIG_KSU_SUSFS=y`)**:
  - **Path Hiding (`sus_path`)**: Hides custom root paths and overlay directories from user application processes.
  - **Mount Hiding (`sus_mount`)**: Filters suspicious mount points from `/proc/self/mounts`, `/proc/self/mountinfo`, and `/proc/self/mountstats`.
  - **Stat / Inode Spoofing (`sus_kstat`)**: Spoofs inode numbers, device numbers, and metadata for overlayed and bind-mounted partitions.
  - **Try-Unmount (`try_umount`)**: Automatically unmounts sensitive paths from namespaces of unprivileged/non-root apps.
  - **Dynamic Uname Spoofing (`spoof_uname`)**: Allows live userspace spoofing of `uname -r` / `/proc/version` strings on the fly.
  - **Open Redirection (`open_redirect`)**: Transparently redirects sensitive filesystem accesses.
  - **Kallsyms Protection (`hide_ksu_susfs_symbols`)**: Strips KernelSU and SuSFS internal symbols from `/proc/kallsyms`.
  - **Standard Syscall Dispatcher**: Communicates directly through `prctl(KERNEL_SU_OPTION, ...)` in `kernel/sys.c`, fully compatible with official `ksu_susfs` userspace binaries and Magisk/KernelSU modules.
- **Integrated KernelSU-Next (v3.3.0 / 33214)**:
  - Full manual source hooks (`fs/exec.c`, `fs/open.c`, `fs/stat.c`, `fs/read_write.c`, `drivers/input/input.c`, `kernel/reboot.c`).
  - Kernel-level su domain authorization, completely invisible to userspace root detectors.
  - Packaged with clean, unpatched factory stock Samsung ramdisk (zero Magisk conflicts).
- **Samsung KABI & MediaTek Task Turbo Protection**:
  - `futex_exit_mutex` preserved across `struct task_struct` reserve slots 3-6 to eliminate scheduler panics on Helio G85.
- **Anti-Detection Build Spoofing**:
  - Builder spoofed to authentic factory string: `dpi@21DKGB11`.
  - Zero `-dirty` git tags and zero custom commit hashes in `/proc/version`.
  - Exact stock version: `4.19.191-29401052-abA065FXXS4AYE2`.
- **Stripped DWARF Debug Info (`CONFIG_DEBUG_INFO`)**:
  - Reduced `vmlinux` memory footprint from **276 MB down to 37 MB**.
- **Stripped Samsung DEFEX Anti-Tamper**:
  - Completely eliminates Samsung's kernel-level process killer (`fs/exec.c`) for smooth context switching.
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
| `boot_custom.img` / `boot_custom_susfs.img` | 64 MB | Repacked Android boot v2 image (KernelSU-Next v3.3.0 + SuSFS v1.5.5, clean ramdisk + SEANDROIDENFORCE footer). Ready for Heimdall or `dd`. |
| `AP_custom_kernel_AYE2.tar` / `AP_custom_kernel_susfs_AYE2.tar` | 65 MB | Odin-flashable archive containing `boot.img` and `vbmeta.img`. Flash via Odin **AP** slot. |
| `ksu_module_susfs_v1.5.5.zip` | 185 KB | Companion SuSFS v1.5.5 module for KernelSU Next Manager. |
| `Image.gz` | 12.5 MB | Gzip-compressed kernel binary for AnyKernel3 or custom repacking. |
| `Image` | 30 MB | Raw uncompressed AArch64 kernel binary. |
| `KernelSU_Next_v3.3.0.apk` | 9.8 MB | Companion KernelSU Next Manager application. |
| `sha256sums.txt` | Text | SHA-256 integrity checksums. |

### SHA-256 Checksums
```text
fe4ae4c8a9361e40cbacc2c074e101a7d3084c568ee8adc8ebae0d1557b8db84  Image
c1770b7791f24b457ea0c4cb0bd3ff8ce7c5b11e2543b5e7dbb7cd489d99de59  Image.gz
9580ec1fcd41286d13ff8b9e668a2c64c959cfb00b49bbdaf9e4bd17e23fa0b0  boot_custom.img
9580ec1fcd41286d13ff8b9e668a2c64c959cfb00b49bbdaf9e4bd17e23fa0b0  boot_custom_susfs.img
2a020f46571e05618081c644855867e27df8451d755cdff46ecfbd91dd3a1fcd  AP_custom_kernel_AYE2.tar
2a020f46571e05618081c644855867e27df8451d755cdff46ecfbd91dd3a1fcd  AP_custom_kernel_susfs_AYE2.tar
f4c8f821eb5d8a4208602c91d4f77925a8222dabe0352a9a5772bb24caf9ca90  ksu_module_susfs_v1.5.5.zip
fd0b12385c98fe9d5f4f1257b5f184e55c74c1376637507df0718305f5d7a924  KernelSU_Next_v3.3.0.apk
```

---

## 🛠️ Flashing Guide

### Method 1: Direct Shell (If Already Rooted)
```bash
adb push boot_custom.img /data/local/tmp/
adb shell "su -c 'dd if=/data/local/tmp/boot_custom.img of=/dev/block/by-name/boot bs=4096 && sync && reboot'"
```

### Method 2: Heimdall (Linux CLI)
Reboot phone into Download Mode:
```bash
adb reboot download
heimdall flash --pit a06.pit --boot boot_custom.img
```

### Method 3: Odin (Windows PC)
1. Reboot phone into Download Mode.
2. Select `AP_custom_kernel_AYE2.tar` in the **AP** slot.
3. Click **Start**.

### Installing SuSFS Companion Module
After booting into Android with KernelSU Next:
1. Open **KernelSU Next Manager** application.
2. Navigate to **Modules** tab.
3. Tap **Install** and select `ksu_module_susfs_v1.5.5.zip` (or run `ksud module install /path/to/ksu_module_susfs_v1.5.5.zip` via root shell).
4. Reboot the device to activate SuSFS hiding hooks.

---

## ❤️ Credits & Acknowledgements
- **Samsung Open Source Release Center (OSRC)** for stock source code (`A065FXXS4AYE2`).
- **simonpunk** for the original SuSFS (`susfs4ksu`) architecture.
- **tiann** (KernelSU author) & **rifsxd / pershoot** (KernelSU-Next team).
- **physwizz** for Helio G85 kernel research & governor optimizations.
- **topjohnwu & The Magisk Team**.
- **bmax121 & The APatch Team**.
