# Full Kernel Compilation Guide — SM-A065F (MT6769V / Linux 4.19.191)

Complete step-by-step kernel build workflow for the Samsung Galaxy A06.
Output: boot_custom.img ready for Odin/Heimdall flashing.

---

## 0. Prerequisites

Run HOST_SETUP.md first. Verify:
```bash
clang-17 --version    # Must be 17.x.x
aarch64-linux-gnu-gcc --version
pahole --version
```

---

## 1. Clone the Kernel Source

```bash
# Your production kernel repo (already published with all patches applied):
git clone https://github.com/s47user/android_kernel_samsung_a06.git kernel-source
cd kernel-source

# Alternatively, start from Samsung OSRC (raw stock source):
# Package: SM-A065F_14_Opensource_A065FXXS4AYE2_A065MUBS4AYD2.zip
# URL: https://opensource.samsung.com/uploadSearch?searchValue=SM-A065F
# Extract: unzip SM-A065F_14_Opensource*.zip && tar xf Kernel.tar.gz
```

---

## 2. Build Environment Variables

Export these before every build. Put in a `build_env.sh` to source:

```bash
export ARCH=arm64
export SUBARCH=arm64

# Clang cross-compiler (LLVM full toolchain)
export CC=clang-17
export LD=ld.lld-17
export AR=llvm-ar-17
export NM=llvm-nm-17
export OBJCOPY=llvm-objcopy-17
export OBJDUMP=llvm-objdump-17
export STRIP=llvm-strip-17

# GNU binutils for cross-assembly
export CROSS_COMPILE=aarch64-linux-gnu-
export CROSS_COMPILE_ARM32=arm-linux-gnueabi-

# Anti-detection identity spoofing
export KBUILD_BUILD_USER="dpi"
export KBUILD_BUILD_HOST="21DKGB11"
export LOCALVERSION=""

# Output directory (keep source tree clean)
export OUT_DIR=$(pwd)/out
mkdir -p $OUT_DIR
```

---

## 3. Apply KernelSU-Next Patches (if building from OSRC source)

> Skip this if cloning from s47user/android_kernel_samsung_a06 — already applied.

```bash
# Download KernelSU-Next for non-GKI (manual hook version)
curl -LSs "https://raw.githubusercontent.com/rifsxd/KernelSU-Next/next/kernel/setup.sh" | bash -s next

# This creates: drivers/kernelsu/ and patches:
#   fs/exec.c       — bprm_fill_uid hook
#   fs/open.c       — faccessat hook
#   fs/stat.c       — newfstatat hook
#   fs/read_write.c — read hook
#   drivers/input/input.c — input_handle_event hook
#   kernel/reboot.c — sys_reboot hook
```

## 4. Apply SuSFS Patches (if building from OSRC source)

> Skip if cloning from s47user/android_kernel_samsung_a06 — already applied.

```bash
# SuSFS v1.5.5 for KernelSU
git clone https://github.com/simonpunk/susfs4ksu.git /tmp/susfs

# Apply kernel patches
cp /tmp/susfs/kernel_patches/fs/* fs/
cp /tmp/susfs/kernel_patches/include/linux/* include/linux/
cp /tmp/susfs/kernel_patches/drivers/* drivers/

# Apply KSU side patches (for syscall dispatcher)
patch -p1 < /tmp/susfs/kernel_patches/add_sus_su_support_to_ksu.patch

# Verify SuSFS files added:
ls fs/susfs.c include/linux/susfs.h
```

---

## 5. Apply Physwizz Optimizations Config

```bash
# Merge the optimization config on top of base defconfig
cd kernel-source
scripts/kconfig/merge_config.sh \
  arch/arm64/configs/a06_defconfig \
  ../configs/physwizz_kernel_optimizations.config \
  -o arch/arm64/configs/a06_custom_defconfig
```

---

## 6. Configure the Kernel

```bash
# Load the A06 defconfig into OUT_DIR
make O=$OUT_DIR ARCH=arm64 a06_defconfig

# Optional: open menuconfig to inspect/change individual flags
make O=$OUT_DIR ARCH=arm64 menuconfig

# Verify critical flags are set after defconfig:
grep -E "CONFIG_KSU|CONFIG_KPROBES|CONFIG_WIREGUARD|CONFIG_SECURITY_DEFEX|CONFIG_DEBUG_INFO|CONFIG_ZRAM" \
  $OUT_DIR/.config
# Expected:
#   CONFIG_KSU=y
#   CONFIG_KSU_MANUAL_HOOK=y
#   CONFIG_KPROBES=y
#   CONFIG_WIREGUARD=y
#   # CONFIG_SECURITY_DEFEX is not set
#   # CONFIG_DEBUG_INFO is not set
#   CONFIG_ZRAM=y
```

---

## 7. Build the Kernel

```bash
# Full build — uses all CPU cores
time make O=$OUT_DIR \
  ARCH=arm64 \
  CC=clang-17 \
  LD=ld.lld-17 \
  AR=llvm-ar-17 \
  NM=llvm-nm-17 \
  OBJCOPY=llvm-objcopy-17 \
  STRIP=llvm-strip-17 \
  CROSS_COMPILE=aarch64-linux-gnu- \
  KBUILD_BUILD_USER=dpi \
  KBUILD_BUILD_HOST=21DKGB11 \
  LOCALVERSION="" \
  -j$(nproc) Image.gz

# Expected build time: ~15-25 minutes on a modern x86_64 host
# Output: out/arch/arm64/boot/Image.gz
# Output: out/vmlinux (full ELF, ~37 MB without debug info)
```

---

## 8. Post-Build Verification

```bash
# 1. Verify Image.gz exists and is sane size
ls -lh $OUT_DIR/arch/arm64/boot/Image.gz
# Expected: ~12-13 MB

# 2. Verify /proc/version string (check anti-detection spoofing)
strings $OUT_DIR/vmlinux | grep "Linux version"
# Must show: Linux version 4.19.191-29401052-abA065FXXS4AYE2 (dpi@21DKGB11)
# Must NOT contain: -dirty or any git hash

# 3. Verify DEFEX is gone
strings $OUT_DIR/vmlinux | grep -i defex
# Must return nothing

# 4. Verify KernelSU symbols present
strings $OUT_DIR/vmlinux | grep "kernelsu"
# Should show ksu internal symbols (will be hidden from /proc/kallsyms by SuSFS)

# 5. Verify KABI struct layout (critical for MTK Task Turbo)
pahole -C task_struct $OUT_DIR/vmlinux | grep -A6 "__reserved"
# Compare slot 3-6 offsets against stock AYE2 vmlinux
# Offsets must be identical — if they differ, the kernel will panic on context switch

# 6. Verify SuSFS symbols
strings $OUT_DIR/vmlinux | grep "susfs"
# Should show susfs internal functions
```

---

## 9. Repack into boot.img

```bash
cd "/home/lenovo/ROM AND CUSTOM OS PORTING"

# Unpack the clean stock boot.img (ramdisk must NOT be Magisk-patched)
python3 tools/repack_boot.py unpack boot.img --out boot_unpacked/

# Replace kernel with fresh build
cp kernel-source/$OUT_DIR/arch/arm64/boot/Image.gz boot_unpacked/

# Repack
python3 tools/repack_boot.py repack boot_unpacked/ \
  --kernel boot_unpacked/Image.gz \
  --out boot_custom_new.img

# MANDATORY: Verify SEANDROIDENFORCE footer
tail -c 17 boot_custom_new.img | xxd
# Must show: 53 45 41 4e 44 52 4f 49 44 45 4e 46 4f 52 43 45

# Verify size (must match boot partition: 64 MB)
wc -c boot_custom_new.img
# Must be: 67108864

# Generate SHA-256 and update sha256sums.txt
sha256sum boot_custom_new.img Image.gz $OUT_DIR/Image
```

---

## 10. Package for Odin

```bash
# Package boot + vbmeta into Odin-flashable tar
python3 tools/vbmeta_tool.py pack \
  --boot boot_custom_new.img \
  --vbmeta vbmeta_disabled.img \
  -o AP_custom_kernel_AYE2_new.tar

# Final checksum
sha256sum AP_custom_kernel_AYE2_new.tar
```

---

## 11. Incremental Rebuild (Faster)

After changing only defconfig flags, no full rebuild needed:

```bash
# Just rebuild the kernel image without re-running configure:
make O=$OUT_DIR ARCH=arm64 CC=clang-17 LD=ld.lld-17 \
  CROSS_COMPILE=aarch64-linux-gnu- \
  KBUILD_BUILD_USER=dpi KBUILD_BUILD_HOST=21DKGB11 \
  LOCALVERSION="" \
  -j$(nproc) Image.gz 2>&1 | tail -20
```

---

## 12. Common Build Errors

| Error | Cause | Fix |
|:---|:---|:---|
| `clang: error: unknown argument '-mno-global-merge'` | Wrong Clang version | Use clang-17 exactly |
| `undefined reference to __stack_chk_guard` | Missing libgcc for cross-compile | Install gcc-aarch64-linux-gnu |
| `scripts/gcc-version.sh: line X: aarch64-linux-gnu-gcc: not found` | Missing cross binutils | `apt install gcc-aarch64-linux-gnu` |
| `pahole: DWARF info not found` | CONFIG_DEBUG_INFO is not set | Expected — pahole needs debug info; use a debug build for struct inspection only |
| `BTF: .tmp_vmlinux.btf: pahole (pahole) is not available` | dwarves not installed | `apt install dwarves` |
| Build succeeds but `/proc/version` shows `-dirty` | LOCALVERSION_AUTO=y or git dirty | Add `# CONFIG_LOCALVERSION_AUTO is not set` to defconfig |
| Image.gz is 30+ MB (too large) | CONFIG_DEBUG_INFO not disabled | Verify `# CONFIG_DEBUG_INFO is not set` in .config |
