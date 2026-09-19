#!/usr/bin/env python3
"""
package_recovery.py - Automated Odin Recovery Packager for Samsung Galaxy A06 (SM-A065F)
Processes compiled TWRP / OrangeFox recovery image:
  1. Validates Android Boot Header v2 and partition constraints.
  2. Ensures Samsung SEANDROIDENFORCE signature compliance.
  3. Compresses to recovery.img.lz4.
  4. Generates an Odin-flashable recovery.tar.md5 with MD5 integrity footer.
"""

import os
import sys
import math
import struct
import tarfile
import hashlib
import argparse
import subprocess

PAGE_SIZE = 2048
PARTITION_SIZE = 89128960  # 85.0 MB from a06.pit
SAMSUNG_SEANDROID = b"SEANDROIDENFORCE\x00\x00\x00\x00"
LZ4_BIN = "tools/bin_tools/usr/bin/lz4"

def page_align(size, page=PAGE_SIZE):
    return int(math.ceil(size / page)) * page

def sign_and_pad_recovery(input_img, output_img, target_size=PARTITION_SIZE):
    with open(input_img, "rb") as f:
        data = f.read()

    if data[:8] != b"ANDROID!":
        raise ValueError(f"Invalid Android Boot Header magic: {data[:8]}")

    h_ver = struct.unpack("<I", data[40:44])[0]
    print(f"[*] Recovery Boot Header Version: {h_ver}")
    print(f"[*] Input Recovery Size: {len(data):,} bytes ({len(data)/(1024*1024):.2f} MB)")

    # If already padded to partition size, calculate actual payload size from header
    (
        k_size, k_addr,
        r_size, r_addr,
        s_size, s_addr,
        t_addr, p_size,
        h_ver, os_ver
    ) = struct.unpack("<IIIIIIIIII", data[8:48])
    dtb_size = struct.unpack("<I", data[1648:1652])[0] if h_ver >= 2 else 0
    k_pages = page_align(k_size, p_size)
    r_pages = page_align(r_size, p_size)
    dtb_pages = page_align(dtb_size, p_size)
    payload_end = p_size + k_pages + r_pages + dtb_pages
    if len(data) > payload_end:
        print(f"[*] Trimming existing padding/footer from {len(data):,} down to actual payload: {payload_end:,} bytes")
        data = data[:payload_end]

    # Check if SEANDROIDENFORCE signature exists
    if b"SEANDROIDENFORCE" in data:
        print("[+] SEANDROIDENFORCE signature already present.")
        signed_data = data
    else:
        print("[+] Appending SEANDROIDENFORCE signature...")
        # 16-byte alignment before signature
        align_16 = (16 - (len(data) % 16)) % 16
        signed_data = data + (b"\x00" * align_16) + SAMSUNG_SEANDROID

    if len(signed_data) > target_size:
        raise ValueError(f"Signed recovery image exceeds partition size! ({len(signed_data)} > {target_size})")

    # Pad to target partition size
    padding = target_size - len(signed_data)
    final_data = signed_data + (b"\x00" * padding)

    with open(output_img, "wb") as f:
        f.write(final_data)

    print(f"[✓] Signed & padded image saved: {output_img} ({len(final_data):,} bytes)")
    return output_img

def compress_lz4(src_path, dst_path):
    print(f"[*] Compressing {src_path} -> {dst_path}...")
    cmd = [LZ4_BIN, "-B6", "--content-size", "-f", src_path, dst_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"LZ4 compression failed: {res.stderr}")
    sz = os.path.getsize(dst_path)
    print(f"    Done! Size: {sz:,} bytes ({sz / (1024*1024):.2f} MB)")
    return dst_path

def build_odin_tar(image_path, arc_name, output_md5):
    tar_name = output_md5[:-4] if output_md5.endswith(".md5") else output_md5 + ".tar"
    if os.path.exists(tar_name): os.remove(tar_name)
    if os.path.exists(output_md5): os.remove(output_md5)

    print(f"[*] Packaging {arc_name} into {output_md5}...")
    with tarfile.open(tar_name, "w", format=tarfile.GNU_FORMAT) as tar:
        tar.add(image_path, arcname=arc_name)

    # Compute MD5 checksum
    md5 = hashlib.md5()
    with open(tar_name, "rb") as f:
        while chunk := f.read(16 * 1024 * 1024):
            md5.update(chunk)
    digest = md5.hexdigest()
    print(f"    MD5 Checksum: {digest}")

    with open(tar_name, "ab") as f:
        f.write(f"{digest}  {tar_name}\n".encode("utf-8"))

    os.rename(tar_name, output_md5)
    print(f"[✓] Ready for Odin: {output_md5} ({os.path.getsize(output_md5):,} bytes)")

def main():
    parser = argparse.ArgumentParser(description="Package custom recovery for Samsung Odin")
    parser.add_argument("recovery_img", help="Path to compiled recovery.img")
    parser.add_argument("-o", "--output", default="recovery_custom.tar.md5", help="Output .tar.md5 file")
    parser.add_argument("--compress", action="store_true", help="Compress inside tar as recovery.img.lz4 (Odin standard)")

    args = parser.parse_args()

    signed_img = "work_recovery/recovery_signed.img"
    os.makedirs("work_recovery", exist_ok=True)

    sign_and_pad_recovery(args.recovery_img, signed_img)

    if args.compress:
        lz4_img = "work_recovery/recovery.img.lz4"
        compress_lz4(signed_img, lz4_img)
        build_odin_tar(lz4_img, "recovery.img.lz4", args.output)
    else:
        build_odin_tar(signed_img, "recovery.img", args.output)

if __name__ == "__main__":
    main()
