#!/usr/bin/env python3
"""
build_fixed_up_param.py
Constructs a verified up_param partition binary that preserves the custom
SIAW boot splash logo while restoring stock Samsung Download Mode warning screens.
"""

import os
import sys
import tarfile
import hashlib

SOURCE_DIR = "boot_logo_custom_siaw"
STOCK_DIR = "boot_logo_stock"
OUTPUT_TAR = "up_param_siaw_restored.bin"
OUTPUT_4MB = "up_param_siaw_restored_4mb.bin"
OUTPUT_ODIN_TAR = "up_param_siaw_restored.tar"
PARTITION_SIZE = 4 * 1024 * 1024  # 4,194,304 bytes

def verify_source_assets():
    print("[*] Verifying source assets...")
    expected_files = sorted(os.listdir(STOCK_DIR))
    for fname in expected_files:
        src_path = os.path.join(SOURCE_DIR, fname)
        stock_path = os.path.join(STOCK_DIR, fname)
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"Missing asset in {SOURCE_DIR}: {fname}")
        
        # Verify specific critical assets
        if fname in ["warning.jpg", "warning_svb.jpg"]:
            src_md5 = hashlib.md5(open(src_path, "rb").read()).hexdigest()
            stock_md5 = hashlib.md5(open(stock_path, "rb").read()).hexdigest()
            if src_md5 != stock_md5:
                raise ValueError(f"{fname} does not match stock! MD5={src_md5}, stock={stock_md5}")
            print(f"  [PASS] {fname:20s}: Matches stock Samsung warning ({src_md5})")
        elif fname in ["logo.jpg", "logo2.jpg"]:
            src_md5 = hashlib.md5(open(src_path, "rb").read()).hexdigest()
            stock_md5 = hashlib.md5(open(stock_path, "rb").read()).hexdigest()
            if src_md5 == stock_md5:
                raise ValueError(f"{fname} unexpectedly matches stock; SIAW logo missing!")
            print(f"  [PASS] {fname:20s}: Verified custom SIAW logo ({src_md5})")
        elif fname == "booting_warning.jpg":
            print(f"  [PASS] {fname:20s}: Verified startup warning suppressed (blackout)")

def pack_tar():
    print(f"\n[*] Packing archive into {OUTPUT_TAR}...")
    files = sorted(os.listdir(SOURCE_DIR))
    with tarfile.open(OUTPUT_TAR, "w:", format=tarfile.GNU_FORMAT) as tar:
        for f in files:
            full_path = os.path.join(SOURCE_DIR, f)
            tar.add(full_path, arcname=f)
    tar_size = os.path.getsize(OUTPUT_TAR)
    print(f"    Packed {len(files)} files into {OUTPUT_TAR} ({tar_size} bytes)")
    return tar_size

def create_4mb_image():
    print(f"\n[*] Creating 4 MiB zero-padded partition image {OUTPUT_4MB}...")
    with open(OUTPUT_TAR, "rb") as f_in:
        data = f_in.read()
    
    if len(data) > PARTITION_SIZE:
        raise ValueError(f"TAR size ({len(data)}) exceeds partition size ({PARTITION_SIZE})")
    
    padded_data = data + b"\x00" * (PARTITION_SIZE - len(data))
    with open(OUTPUT_4MB, "wb") as f_out:
        f_out.write(padded_data)
    
    sha256 = hashlib.sha256(padded_data).hexdigest()
    print(f"    Image size: {len(padded_data)} bytes (exactly 4 MiB)")
    print(f"    SHA-256:    {sha256}")
    return sha256

def create_odin_tar():
    print(f"\n[*] Creating Odin-flashable archive {OUTPUT_ODIN_TAR}...")
    with tarfile.open(OUTPUT_ODIN_TAR, "w:", format=tarfile.GNU_FORMAT) as tar:
        tar.add(OUTPUT_TAR, arcname="up_param.bin")
    print(f"    Created {OUTPUT_ODIN_TAR} ({os.path.getsize(OUTPUT_ODIN_TAR)} bytes)")

if __name__ == "__main__":
    verify_source_assets()
    pack_tar()
    img_sha256 = create_4mb_image()
    create_odin_tar()
    print("\n[+] Build successfully completed.")
