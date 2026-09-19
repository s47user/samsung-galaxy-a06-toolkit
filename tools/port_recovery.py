#!/usr/bin/env python3
"""
port_recovery.py - Automated Custom Recovery Binary Porting Engine
Designed for Samsung Galaxy A06 (SM-A065F) | Helio G85 MT6769 | Android 14 One UI 6.1

Ports TWRP or OrangeFox ramdisk from a donor recovery image or zip:
  1. Extracts donor recovery.img from zip (if zip is provided).
  2. Unpacks donor ramdisk (cpio).
  3. Preserves donor recovery UI engine, binaries (recovery, adbd, twres).
  4. Injects Samsung Galaxy A06 hardware configuration:
       - Authentic stock A06 Linux 4.19.191 kernel (Image.gz)
       - Authentic stock A06 DTB table (v2 boot header compatible)
       - A06 EROFS dynamic partition mounts (recovery.fstab & twrp.flags)
       - A06 device identification properties (SM-A065F / a06)
       - MediaTek & Samsung init scripts (init.recovery.mt6768.rc / samsung.rc)
  5. Repacks with Android Boot Image Header v2.
  6. Appends Samsung SEANDROIDENFORCE signature and builds Odin .tar.md5.
"""

import os
import sys
import shutil
import zipfile
import tarfile
import hashlib
import struct
import math
import subprocess
import argparse

# Hardware & Boot Header Configuration
PAGE_SIZE = 2048
PARTITION_SIZE = 89128960  # 85.0 MB from a06.pit
SAMSUNG_SEANDROID = b"SEANDROIDENFORCE\x00\x00\x00\x00"

KERNEL_BASE = 0x40000000
KERNEL_ADDR = 0x40080000
RAMDISK_ADDR = 0x47c80000
TAGS_ADDR = 0x4bc80000
DTB_ADDR = 0x41f78000
HEADER_VERSION = 2
OS_VERSION = 402654780
CMDLINE = b"bootopt=64S3,32N2,64N2 buildvariant=eng"

LZ4_BIN = "tools/bin_tools/usr/bin/lz4"
PREBUILT_DIR = "device/samsung/a06/prebuilt"
STOCK_KERNEL = os.path.join(PREBUILT_DIR, "kernel")
STOCK_DTB = os.path.join(PREBUILT_DIR, "dtb.img")
DEVICE_TREE_DIR = "device/samsung/a06"

def page_align(size, page=PAGE_SIZE):
    return int(math.ceil(size / page)) * page

def extract_donor(donor_path, work_dir):
    """Extracts recovery.img from donor path (handling both raw .img and .zip)"""
    os.makedirs(work_dir, exist_ok=True)
    if donor_path.endswith(".zip"):
        print(f"[*] Extracting donor recovery.img from archive: {donor_path}...")
        with zipfile.ZipFile(donor_path, "r") as z:
            # Look for recovery.img
            for name in z.namelist():
                if name.endswith("recovery.img"):
                    out_path = os.path.join(work_dir, "donor_recovery.img")
                    with z.open(name) as src, open(out_path, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    print(f"    Found and extracted {name} -> {out_path}")
                    return out_path
        raise FileNotFoundError("Could not find recovery.img inside the provided zip archive.")
    elif donor_path.endswith(".img") or donor_path.endswith(".bin"):
        out_path = os.path.join(work_dir, "donor_recovery.img")
        shutil.copyfile(donor_path, out_path)
        return out_path
    else:
        raise ValueError(f"Unsupported donor file format: {donor_path}. Provide a .img or .zip file.")

def unpack_recovery_image(img_path, work_dir):
    """Unpacks boot/recovery header and extracts ramdisk"""
    with open(img_path, "rb") as f:
        raw = f.read()

    if raw[:8] != b"ANDROID!":
        raise ValueError(f"Invalid boot image header magic: {raw[:8]}")

    hdr = raw[:PAGE_SIZE]
    (
        k_size, k_addr,
        r_size, r_addr,
        s_size, s_addr,
        t_addr, p_size,
        h_ver, os_ver
    ) = struct.unpack("<IIIIIIIIII", hdr[8:48])

    print(f"[*] Donor Header Version: {h_ver}, Page Size: {p_size}")
    print(f"[*] Donor Ramdisk Size:   {r_size:,} bytes ({r_size/(1024*1024):.2f} MB)")

    k_offset = p_size
    k_pages = page_align(k_size, p_size)

    r_offset = k_offset + k_pages
    ramdisk_data = raw[r_offset:r_offset + r_size]

    ramdisk_cpio_gz = os.path.join(work_dir, "ramdisk_donor.cpio.gz")
    with open(ramdisk_cpio_gz, "wb") as f:
        f.write(ramdisk_data)

    return ramdisk_cpio_gz

def unpack_ramdisk(cpio_gz_path, ramdisk_dir):
    """Decompresses and extracts ramdisk cpio archive"""
    if os.path.exists(ramdisk_dir):
        shutil.rmtree(ramdisk_dir)
    os.makedirs(ramdisk_dir, exist_ok=True)

    print(f"[*] Extracting donor ramdisk into {ramdisk_dir}...")
    abs_cpio = os.path.abspath(cpio_gz_path)
    cmd = f"gzip -dc '{abs_cpio}' | cpio -idm"
    subprocess.run(cmd, shell=True, cwd=ramdisk_dir, check=True, stderr=subprocess.DEVNULL)

def patch_ramdisk(ramdisk_dir):
    """Injects Samsung Galaxy A06 configurations and fstab into ramdisk"""
    print("[*] Injecting Samsung Galaxy A06 device configs into ramdisk...")

    # 1. Inject recovery.fstab & twrp.flags
    etc_dir = os.path.join(ramdisk_dir, "system", "etc")
    if not os.path.exists(etc_dir):
        etc_dir = os.path.join(ramdisk_dir, "etc")
    os.makedirs(etc_dir, exist_ok=True)

    src_fstab = os.path.join(DEVICE_TREE_DIR, "recovery/root/system/etc/recovery.fstab")
    src_flags = os.path.join(DEVICE_TREE_DIR, "recovery/root/system/etc/twrp.flags")
    shutil.copyfile(src_fstab, os.path.join(etc_dir, "recovery.fstab"))
    shutil.copyfile(src_flags, os.path.join(etc_dir, "twrp.flags"))
    print("    [+] Injected A06 recovery.fstab and twrp.flags")

    # 2. Inject rc scripts
    src_rc_mtk = os.path.join(DEVICE_TREE_DIR, "recovery/root/init.recovery.mt6768.rc")
    src_rc_sam = os.path.join(DEVICE_TREE_DIR, "recovery/root/init.recovery.samsung.rc")
    shutil.copyfile(src_rc_mtk, os.path.join(ramdisk_dir, "init.recovery.mt6768.rc"))
    shutil.copyfile(src_rc_sam, os.path.join(ramdisk_dir, "init.recovery.samsung.rc"))
    print("    [+] Injected init.recovery.mt6768.rc and init.recovery.samsung.rc")

    # 3. Patch prop.default with A06 identifiers
    prop_file = os.path.join(ramdisk_dir, "prop.default")
    if not os.path.exists(prop_file):
        prop_file = os.path.join(ramdisk_dir, "default.prop")

    if os.path.exists(prop_file):
        with open(prop_file, "r", errors="ignore") as f:
            lines = f.readlines()

        new_lines = []
        override_keys = {
            "ro.product.device": "a06",
            "ro.product.model": "SM-A065F",
            "ro.product.brand": "samsung",
            "ro.product.name": "a06xx",
            "ro.product.board": "a06",
            "ro.build.product": "a06",
        }
        for line in lines:
            line_strip = line.strip()
            matched = False
            for k, v in override_keys.items():
                if line_strip.startswith(f"{k}="):
                    new_lines.append(f"{k}={v}\n")
                    matched = True
                    break
            if not matched:
                new_lines.append(line)

        with open(prop_file, "w") as f:
            f.writelines(new_lines)
        print("    [+] Patched device identity props (ro.product.device=a06, SM-A065F)")

def repack_ramdisk(ramdisk_dir, output_cpio_gz):
    """Repacks modified ramdisk into gzip cpio"""
    print(f"[*] Repacking ramdisk archive -> {output_cpio_gz}...")
    cmd = f"find . | cpio -o -H newc -R 0:0 | gzip -9 > '{os.path.abspath(output_cpio_gz)}'"
    subprocess.run(cmd, shell=True, cwd=ramdisk_dir, check=True)
    sz = os.path.getsize(output_cpio_gz)
    print(f"    Done! Ramdisk size: {sz:,} bytes ({sz/(1024*1024):.2f} MB)")
    return output_cpio_gz

def build_boot_v2_image(kernel_path, ramdisk_path, dtb_path, output_img, target_size=PARTITION_SIZE):
    """Builds an authentic Android Boot Image v2 matching Samsung LittleKernel specs"""
    print("[*] Assembling Android Boot Image v2...")

    with open(kernel_path, "rb") as f:
        kernel = f.read()
    with open(ramdisk_path, "rb") as f:
        ramdisk = f.read()
    with open(dtb_path, "rb") as f:
        dtb = f.read()

    k_size = len(kernel)
    r_size = len(ramdisk)
    dtb_size = len(dtb)

    # Boot image header v2 (PAGE_SIZE = 2048)
    hdr = bytearray(PAGE_SIZE)
    # Magic
    hdr[0:8] = b"ANDROID!"
    # Fields: kernel_size, kernel_addr, ramdisk_size, ramdisk_addr, second_size, second_addr, tags_addr, page_size, header_version, os_version
    struct.pack_into("<IIIIIIIIII", hdr, 8,
                     k_size, KERNEL_ADDR,
                     r_size, RAMDISK_ADDR,
                     0, 0,
                     TAGS_ADDR, PAGE_SIZE,
                     HEADER_VERSION, OS_VERSION)

    # Cmdline
    hdr[64:64+len(CMDLINE)] = CMDLINE

    # v2 offsets: recovery_dtbo_size(4), recovery_dtbo_offset(8), header_size(4), dtb_size(4), dtb_addr(8)
    header_size = 1660
    struct.pack_into("<IQIIQ", hdr, 1632, 0, 0, header_size, dtb_size, DTB_ADDR)

    # Assemble: Header + Kernel + Ramdisk + DTB
    out = bytearray(hdr)
    out += kernel
    out += b"\x00" * (page_align(k_size, PAGE_SIZE) - k_size)

    out += ramdisk
    out += b"\x00" * (page_align(r_size, PAGE_SIZE) - r_size)

    dtb_block = bytearray(dtb)
    align_16 = (16 - (len(dtb_block) % 16)) % 16
    dtb_block += b"\x00" * align_16
    dtb_block += SAMSUNG_SEANDROID
    out += dtb_block
    out += b"\x00" * (page_align(len(dtb_block), PAGE_SIZE) - len(dtb_block))

    # Pad to partition size
    if len(out) < target_size:
        out += b"\x00" * (target_size - len(out))
    elif len(out) > target_size:
        raise ValueError(f"Image exceeds recovery partition size! ({len(out)} > {target_size})")

    with open(output_img, "wb") as f:
        f.write(out)

    print(f"[✓] Successfully built recovery image: {output_img} ({len(out):,} bytes)")
    return output_img

def build_odin_package(recovery_img_path, output_tar_md5):
    """Compresses with lz4 and creates Odin .tar.md5"""
    work_dir = os.path.dirname(recovery_img_path) or "."
    lz4_path = os.path.join(work_dir, "recovery.img.lz4")

    print(f"[*] Compressing {recovery_img_path} -> {lz4_path}...")
    cmd = [LZ4_BIN, "-B6", "--content-size", "-f", recovery_img_path, lz4_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"LZ4 compression failed: {res.stderr}")

    tar_name = output_tar_md5[:-4] if output_tar_md5.endswith(".md5") else output_tar_md5 + ".tar"
    if os.path.exists(tar_name): os.remove(tar_name)
    if os.path.exists(output_tar_md5): os.remove(output_tar_md5)

    print(f"[*] Creating Odin package: {output_tar_md5}...")
    with tarfile.open(tar_name, "w", format=tarfile.GNU_FORMAT) as tar:
        tar.add(lz4_path, arcname="recovery.img.lz4")

    md5 = hashlib.md5()
    with open(tar_name, "rb") as f:
        while chunk := f.read(16 * 1024 * 1024):
            md5.update(chunk)
    digest = md5.hexdigest()
    print(f"    MD5: {digest}")

    with open(tar_name, "ab") as f:
        f.write(f"\n{digest}  {tar_name}\n".encode("utf-8"))

    os.rename(tar_name, output_tar_md5)
    print(f"[✓] Package Ready: {output_tar_md5} ({os.path.getsize(output_tar_md5)/(1024*1024):.2f} MB)")

def main():
    parser = argparse.ArgumentParser(description="Port TWRP/OrangeFox recovery to Samsung Galaxy A06")
    parser.add_argument("--donor", required=True, help="Path to donor recovery image (.img) or OrangeFox archive (.zip)")
    parser.add_argument("-o", "--output", default="A06_OrangeFox_Recovery.tar.md5", help="Output Odin flashable package (.tar.md5)")
    parser.add_argument("--work-dir", default="work_recovery/port_staging", help="Working staging directory")

    args = parser.parse_args()

    work_dir = args.work_dir
    os.makedirs(work_dir, exist_ok=True)

    donor_img = extract_donor(args.donor, work_dir)
    ramdisk_cpio_gz = unpack_recovery_image(donor_img, work_dir)

    ramdisk_dir = os.path.join(work_dir, "ramdisk_extracted")
    unpack_ramdisk(ramdisk_cpio_gz, ramdisk_dir)

    patch_ramdisk(ramdisk_dir)

    patched_ramdisk = os.path.join(work_dir, "ramdisk_patched.cpio.gz")
    repack_ramdisk(ramdisk_dir, patched_ramdisk)

    output_raw_img = os.path.join(work_dir, "recovery_ported.img")
    build_boot_v2_image(STOCK_KERNEL, patched_ramdisk, STOCK_DTB, output_raw_img)

    build_odin_package(output_raw_img, args.output)

    print("\n========================================================")
    print(" Porting Complete! Ready to Flash via Odin4 or Odin v3")
    print(f" Output File: {args.output}")
    print("========================================================")

if __name__ == "__main__":
    main()
