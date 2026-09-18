#!/usr/bin/env python3
"""
package_rom.py - Automated Odin AP Packaging Engine for Samsung Galaxy A06 (SM-A065F)
Creates a flashable AP_A065F_Debloated_V1.tar.md5 containing:
  - Custom Debloated super.img.lz4 (EROFS)
  - Custom Kernel boot.img.lz4 (KernelSU-Next + SuSFS)
  - Disabled vbmeta.img.lz4 (AVB 2.0 dm-verity disabled)
  - All stock companion trustlets & partitions (dtbo, recovery, gz, scp, spmfw, sspm, tee, tzar)
"""

import os
import sys
import tarfile
import hashlib
import subprocess
import shutil

STOCK_AP_DIR = "ACR-A065FXXS4AYE2-20250519143541/AP_A065FXXS4AYE2_A065FXXS4AYE2_MQB96038222_REV00_user_low_ship_MULTI_CERT_meta_OS14"
WORK_DIR = "work_rom"
PACKAGE_DIR = os.path.join(WORK_DIR, "package_staging")
LZ4_BIN = "tools/bin_tools/usr/bin/lz4"
OUT_TAR = "AP_A065F_Debloated_V1.6.tar"
OUT_TAR_MD5 = "AP_A065F_Debloated_V1.6.tar.md5"
OUT_SUPER_ONLY_TAR = "AP_A065F_Debloated_V1.6_SUPER_ONLY.tar"
OUT_SUPER_ONLY_MD5 = "AP_A065F_Debloated_V1.6_SUPER_ONLY.tar.md5"

COMPANION_BLOBS = [
    "dtbo.img.lz4",
    "recovery.img.lz4",
    "gz-verified.img.lz4",
    "scp-verified.img.lz4",
    "spmfw-verified.img.lz4",
    "sspm-verified.img.lz4",
    "tee-verified.img.lz4",
    "tzar.img.lz4",
    "vbmeta_system.img.lz4",
]

def compress_lz4(src, dst):
    print(f"  [>] Compressing {src} -> {dst}...")
    cmd = [LZ4_BIN, "-B6", "--content-size", "-f", src, dst]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"LZ4 compression failed: {res.stderr}")
    sz = os.path.getsize(dst)
    print(f"      Done! Size: {sz / (1024*1024):.2f} MB")

def build_odin_tar(tar_name, md5_name, file_list):
    print(f"\n[>] Creating archive: {md5_name}...")
    if os.path.exists(tar_name): os.remove(tar_name)
    if os.path.exists(md5_name): os.remove(md5_name)

    with tarfile.open(tar_name, "w", format=tarfile.GNU_FORMAT) as tar:
        for fpath, arcname in file_list:
            sz = os.path.getsize(fpath)
            print(f"  -> Adding {arcname:<25} ({sz / (1024*1024):>7.2f} MB)")
            tar.add(fpath, arcname=arcname)

    print(f"  [+] Calculating MD5 checksum...")
    md5 = hashlib.md5()
    with open(tar_name, "rb") as f:
        while chunk := f.read(16 * 1024 * 1024):
            md5.update(chunk)
    digest = md5.hexdigest()
    print(f"      MD5: {digest}")

    with open(tar_name, "ab") as f:
        f.write(f"\n{digest}  {tar_name}\n".encode("utf-8"))

    os.rename(tar_name, md5_name)
    final_sz = os.path.getsize(md5_name)
    print(f"  [✓] Complete: {md5_name} ({final_sz / (1024*1024):.2f} MB / {final_sz / (1024**3):.2f} GB)")
    return md5_name

def main():
    print("==========================================================")
    print(" Samsung Galaxy A06 (SM-A065F) Odin AP Packager V1.6")
    print("==========================================================\n")

    os.makedirs(PACKAGE_DIR, exist_ok=True)

    # 1. Custom Super Image
    custom_super_lz4 = os.path.join(WORK_DIR, "super.img.lz4")
    if not os.path.exists(custom_super_lz4):
        print(f"[-] Error: {custom_super_lz4} not found! Please build super first.")
        sys.exit(1)
    dst_super = os.path.join(PACKAGE_DIR, "super.img.lz4")
    if not os.path.exists(dst_super) or os.path.getmtime(custom_super_lz4) > os.path.getmtime(dst_super):
        print(f"[1/5] Linking custom super.img.lz4 ({os.path.getsize(custom_super_lz4)/(1024*1024):.1f} MB)...")
        if os.path.exists(dst_super): os.remove(dst_super)
        os.link(custom_super_lz4, dst_super)
    else:
        print(f"[1/5] custom super.img.lz4 already staged.")

    # 2. Custom Kernel (boot.img.lz4)
    custom_boot = "boot_custom_susfs.img"
    if not os.path.exists(custom_boot):
        print(f"[-] Error: {custom_boot} not found!")
        sys.exit(1)
    dst_boot_lz4 = os.path.join(PACKAGE_DIR, "boot.img.lz4")
    print(f"[2/5] Compressing custom kernel: {custom_boot}...")
    compress_lz4(custom_boot, dst_boot_lz4)

    # 3. Disabled VBMeta (vbmeta.img.lz4)
    disabled_vbmeta = "vbmeta_disabled.img"
    if not os.path.exists(disabled_vbmeta):
        print(f"[-] Error: {disabled_vbmeta} not found!")
        sys.exit(1)
    dst_vbmeta_lz4 = os.path.join(PACKAGE_DIR, "vbmeta.img.lz4")
    print(f"[3/5] Compressing disabled vbmeta: {disabled_vbmeta}...")
    compress_lz4(disabled_vbmeta, dst_vbmeta_lz4)

    # 4. Companion Stock Blobs
    print(f"[4/5] Staging companion stock firmware blobs...")
    for blob in COMPANION_BLOBS:
        src = os.path.join(STOCK_AP_DIR, blob)
        dst = os.path.join(PACKAGE_DIR, blob)
        if not os.path.exists(src):
            print(f"  [!] Warning: {src} not found!")
            continue
        if os.path.exists(dst): os.remove(dst)
        os.link(src, dst)
        print(f"  [+] Staged: {blob}")

    # 5. Build SUPER_ONLY package
    print(f"\n[5/6] Packaging SUPER_ONLY archive: {OUT_SUPER_ONLY_MD5}...")
    super_only_files = [
        (dst_super, "super.img.lz4")
    ]
    build_odin_tar(OUT_SUPER_ONLY_TAR, OUT_SUPER_ONLY_MD5, super_only_files)

    # 6. Build Complete V1.2 AP package
    print(f"\n[6/6] Packaging full Odin AP archive: {OUT_TAR_MD5}...")
    files_to_pack = sorted(os.listdir(PACKAGE_DIR))
    full_files = [
        (os.path.join(PACKAGE_DIR, f), f) for f in files_to_pack
    ]
    build_odin_tar(OUT_TAR, OUT_TAR_MD5, full_files)

    print(f"\n==========================================================")
    print(f" [✓] ALL ODIN PACKAGES READY!")
    print(f" 1. SUPER_ONLY : {OUT_SUPER_ONLY_MD5}")
    print(f" 2. FULL AP    : {OUT_TAR_MD5}")
    print(f"==========================================================\n")

if __name__ == "__main__":
    main()
