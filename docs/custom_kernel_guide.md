# Custom Kernel Guide: Samsung Galaxy A06 (KernelSU-Next & Physwizz Architecture)

## 1. Overview
The Galaxy A06 (`SM-A065F`) uses the MediaTek MT6769V (Helio G85) BSP. Its kernel architecture is shared with the Galaxy A05 (`SM-A055F`).

Compiling a custom kernel allows:
1. **KernelSU-Next Integration**: Native kernel-level root via manual source hooks (`CONFIG_KSU=y`, `CONFIG_KSU_MANUAL_HOOK=y`).
2. **Anti-Detection Identity Spoofing**: Matching factory stock Samsung builder (`dpi@21DKGB11`), eliminating the `-dirty` git flag and commit hashes.
3. **Stripping Samsung DEFEX**: Completely eliminates Samsung's kernel-level security process killer.
4. **Stripping Debug Symbols**: Disabling `CONFIG_DEBUG_INFO`, shrinking `vmlinux` from 276 MB down to 37 MB.
5. **Kprobes & APatch KPM**: `CONFIG_KPROBES=y` for dynamic runtime symbol tracing.
6. **Ultra-Fast zRAM**: Defaulting to **LZ4** compression in-RAM, bypassing eMMC 5.1 disk-swap freezes.
7. **BBR & WireGuard**: In-kernel cryptographic WireGuard VPN tunneling and Google BBR TCP pacing.

Official Repository: [s47user/android_kernel_samsung_a06](https://github.com/s47user/android_kernel_samsung_a06.git)

---

## 2. Source Code & Toolchain
- **Source**: Sourced from [opensource.samsung.com](https://opensource.samsung.com) (Package: `SM-A065F_14_Opensource_A065FXXS4AYE2_A065MUBS4AYD2.zip`).
- **Toolchain**:
  - Android NDK r26+ LLVM / Clang 17.0.2 + LLD 17.0.2.
  - GNU GCC AArch64 binutils (`aarch64-linux-gnu-`).
- **Target Defconfig**: `arch/arm64/configs/a06_defconfig`.

---

## 3. Build Spoofing & Anti-Detection Environment
To ensure `/proc/version` perfectly mimics factory Samsung production builds without `-dirty` tags:
```bash
export KBUILD_BUILD_USER="dpi"
export KBUILD_BUILD_HOST="21DKGB11"
export LOCALVERSION=""
```
In `arch/arm64/configs/a06_defconfig`:
```ini
CONFIG_LOCALVERSION="-29401052-abA065FXXS4AYE2"
# CONFIG_LOCALVERSION_AUTO is not set
# CONFIG_DEBUG_INFO is not set
CONFIG_KSU=y
CONFIG_KSU_MANUAL_HOOK=y
```

---

## 4. Building the Kernel
Run the automated build script:
```bash
chmod +x build.sh
./build.sh
```
Output binaries:
- Kernel image: `out/arch/arm64/boot/Image.gz` (approx. 12 MB)
- Uncompressed ELF: `out/vmlinux` (approx. 37 MB)

---

## 5. Repackaging & Flashing

### Repacking `boot_custom.img`
Use `tools/repack_boot.py` with the clean, unpatched factory stock Samsung `boot.img` (ensuring no Magisk hooks exist in ramdisk):
```bash
python3 tools/repack_boot.py --stock boot.img --kernel Image.gz -o boot_custom.img
```

### Flashing via Heimdall (Linux CLI)
Put the phone into Download Mode and execute in a single clean session:
```bash
heimdall flash --pit a06.pit --boot boot_custom.img
```

### Flashing via Odin (Windows PC)
Assemble an Odin-compatible tarball and flash via the **AP** slot:
```bash
tar -cf AP_custom_kernel_AYE2.tar --transform 's|boot_custom.img|boot.img|' --transform 's|vbmeta_disabled.img|vbmeta.img|' boot_custom.img vbmeta_disabled.img
```

---

## 6. Companion Manager
Install the **KernelSU Next Manager** APK (`KernelSU_Next_v3.3.0.apk`) to manage root privileges and app authorization.
