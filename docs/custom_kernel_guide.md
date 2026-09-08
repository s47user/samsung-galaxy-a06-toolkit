# Custom Kernel Guide: Samsung Galaxy A06 (Physwizz Architecture)

## 1. Overview
The Galaxy A06 (`SM-A065F`) uses the MediaTek MT6769V (Helio G85) BSP. Its kernel architecture is shared with the Galaxy A05 (`SM-A055F`).

Compiling a custom kernel (following developer **physwizz**'s methodology) allows:
1. Stripping Samsung's kernel-level **DEFEX** security process killer.
2. Enabling **Kprobes** (`CONFIG_KPROBES`) for dynamic KernelPatch Modules (KPM).
3. Backporting **LZ4 / ZSTD zRAM** compressors.
4. Baking in **WireGuard** (`CONFIG_WIREGUARD=y`) and Google **BBR** TCP congestion control.

---

## 2. Source Code & Toolchain
- **Source**: Sourced from [opensource.samsung.com](https://opensource.samsung.com) (Package: `SM-A065F_14_Opensource_A065FXXS4AYE2_A065MUBS4AYD2.zip`).
- **Toolchain**:
  - Google AOSP Clang (r416183b or r383902, Clang 11/12).
  - GNU GCC AArch64 binutils (`aarch64-linux-gnu-`).
- **Target Defconfig**: `arch/arm64/configs/vendor/a06_eur_open_defconfig` or `mt6769_defconfig`.

---

## 3. Applying the Optimization Matrix
Refer to `configs/physwizz_kernel_optimizations.config` for the full set of config flags.

Key edits:
```ini
# Disables Samsung DEFEX
# CONFIG_SECURITY_DEFEX is not set

# Enables Kprobes for APatch
CONFIG_KPROBES=y
CONFIG_HAVE_KPROBES=y
CONFIG_KPROBE_EVENTS=y

# Enables Fast zRAM
CONFIG_ZRAM=y
CONFIG_ZRAM_DEF_COMP_LZ4=y
CONFIG_ZSMALLOC=y
```

---

## 4. Building the Kernel
```bash
export ARCH=arm64
export SUBARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-
export CC=clang
export CLANG_TRIPLE=aarch64-linux-gnu-

make O=out vendor/a06_eur_open_defconfig
make O=out -j$(nproc)
```

Output binary: `out/arch/arm64/boot/Image.gz` (or `Image.gz-dtb`).

---

## 5. Repackaging into `boot.img`
Use `magiskboot` or `AnyKernel3` to replace the stock kernel binary inside `boot.img` while preserving the stock Samsung ramdisk and device tree table (`dtb`).
