# Host Environment Setup — SM-A065F ROM Development

Complete Linux workstation setup for building and flashing custom ROMs for the A06.
Tested on Ubuntu 22.04 LTS / Debian 12.

---

## 1. Core System Packages

```bash
sudo apt update && sudo apt install -y \
  # ADB + Fastboot
  adb android-tools-adb \
  # Heimdall (Samsung Download Mode flasher)
  heimdall-flash \
  # Build tools
  build-essential git bc bison flex libssl-dev libelf-dev \
  # Clang/LLVM 17 (kernel compiler)
  clang-17 lld-17 llvm-17 \
  # AArch64 cross-compiler (GNU binutils)
  gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu \
  # LZ4 compression (for .img.lz4 Samsung firmware)
  lz4 \
  # Python 3 runtime
  python3 python3-pip python3-construct \
  # Hex inspection tools
  xxd hexyl \
  # EROFS tools (if not using toolkit bin_tools)
  erofs-utils \
  # Kernel struct analysis
  dwarves \
  # Misc
  wget curl unzip tar pv rsync
```

## 2. LLVM/Clang 17 Symlinks (if using distro package)

```bash
# Set clang-17 as default clang
sudo update-alternatives --install /usr/bin/clang   clang   /usr/bin/clang-17   17
sudo update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-17 17
sudo update-alternatives --install /usr/bin/ld.lld  ld.lld  /usr/bin/ld.lld-17  17
sudo update-alternatives --install /usr/bin/llvm-ar llvm-ar /usr/bin/llvm-ar-17  17

# Verify
clang --version    # Must show: clang version 17.x.x
ld.lld --version   # Must show: LLD 17.x.x
```

## 3. Python Toolkit Dependencies

```bash
# Install toolkit Python dependencies
pip3 install construct lz4 requests tqdm

# Verify toolkit scripts are functional
python3 tools/lpunpack.py --help
python3 tools/debloat.py --help
python3 tools/repack_boot.py --help
python3 tools/vbmeta_tool.py --help
python3 tools/logo_tool.py --help
python3 tools/package_rom.py --help
```

## 4. Verify Self-Contained Bin Tools

```bash
# These binaries are pre-compiled and stored in tools/bin_tools/
ls tools/bin_tools/usr/bin/
# Expected: mkfs.erofs  fsck.erofs  dump.erofs  lpmake  lz4

# Make executable and test
chmod +x tools/bin_tools/usr/bin/*
tools/bin_tools/usr/bin/mkfs.erofs --version
tools/bin_tools/usr/bin/lpmake --version
```

## 5. Samsung USB udev Rules

```bash
# Allow non-root ADB + Heimdall access to Samsung devices
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", MODE="0666", GROUP="plugdev"' \
  | sudo tee /etc/udev/rules.d/51-samsung.rules

sudo usermod -aG plugdev $USER
sudo udevadm control --reload-rules && sudo udevadm trigger

# Log out and back in, or run:
newgrp plugdev
```

## 6. Odin4 Setup

```bash
# Odin4 is stored as a binary in the workspace root
chmod +x ./odin4-gui_arm64_7.3.0-a46321b
# Or if using the CLI version symlinked:
sudo cp odin4 /usr/local/bin/odin4
sudo chmod +x /usr/local/bin/odin4

# Test:
sudo odin4 --help
```

## 7. pahole (KABI Verification Tool)

```bash
# pahole is part of the dwarves package (installed above)
pahole --version
# Must show: pahole (pahole) vX.XX

# Test KABI slot inspection after a kernel build:
# pahole -C task_struct out/vmlinux | grep -A10 "__reserved"
```

## 8. Environment Verification Script

Run this to confirm everything is in place before starting a kernel build:

```bash
#!/bin/bash
echo "=== ROM Dev Environment Check ==="
check() { command -v $1 &>/dev/null && echo "OK  $1" || echo "MISS $1"; }
check adb; check heimdall; check clang-17; check ld.lld-17
check aarch64-linux-gnu-gcc; check python3; check lz4; check xxd; check pahole
echo ""
echo "=== Toolkit bin_tools ==="
for t in mkfs.erofs fsck.erofs lpmake lz4; do
  [ -x "tools/bin_tools/usr/bin/$t" ] && echo "OK  $t" || echo "MISS $t"
done
echo ""
echo "=== ADB Device ==="
adb devices
echo ""
echo "=== Clang version ==="
clang-17 --version | head -1
```

## 9. Disk Space Requirements

| Operation | Space Required |
|:---|:---|
| Kernel source clone | ~3 GB |
| Full kernel build output | ~2 GB |
| Firmware extraction (super.img) | ~15 GB (uncompressed) |
| Working super.img rebuild | ~8 GB |
| Full workspace with all artifacts | ~25 GB |

Minimum recommended: **50 GB free disk space** before starting firmware work.

## 10. Recommended Directory Layout

```
~/rom-dev/
├── ROM AND CUSTOM OS PORTING/   ← This workspace (git repo)
├── kernel-source/               ← Cloned kernel tree (3 GB)
│   └── android_kernel_samsung_a06/
└── toolchain/                   ← Optional: standalone Clang if distro version is old
    └── clang-17/
```
