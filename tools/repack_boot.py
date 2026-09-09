#!/usr/bin/env python3
"""
Android Boot Image v2 Unpack & Repack Tool
Designed for Samsung Galaxy A06 (SM-A065F) & MediaTek Helio G85.
Preserves stock ramdisk, DTB table, kernel arguments, and page alignments.
Appends Samsung SEANDROIDENFORCE signature header for seamless bootloader compliance.
"""

import sys
import os
import struct
import math
import argparse

BOOT_MAGIC = b"ANDROID!"
PAGE_SIZE = 2048
PARTITION_SIZE = 67108864  # 64 MB
SAMSUNG_SEANDROID = b"SEANDROIDENFORCE\x00\x00\x00\x00"

def page_align(size, page=PAGE_SIZE):
    return int(math.ceil(size / page)) * page

def unpack_boot(boot_path):
    with open(boot_path, "rb") as f:
        raw = f.read()

    if raw[:8] != BOOT_MAGIC:
        raise ValueError(f"Invalid boot image magic: {raw[:8]}")

    hdr = raw[:PAGE_SIZE]
    (
        k_size, k_addr,
        r_size, r_addr,
        s_size, s_addr,
        t_addr, p_size,
        h_ver, os_ver
    ) = struct.unpack("<IIIIIIIIII", hdr[8:48])

    name = hdr[48:64].split(b"\x00")[0].decode("ascii", errors="ignore")
    cmdline = hdr[64:576].split(b"\x00")[0].decode("ascii", errors="ignore")
    extra_cmdline = hdr[608:1632].split(b"\x00")[0].decode("ascii", errors="ignore")

    recovery_dtbo_size, recovery_dtbo_offset, header_size = struct.unpack("<IQI", hdr[1632:1648])
    dtb_size, dtb_addr = struct.unpack("<IQ", hdr[1648:1660])

    k_offset = p_size
    k_pages = page_align(k_size, p_size)

    r_offset = k_offset + k_pages
    r_pages = page_align(r_size, p_size)

    dtb_offset = r_offset + r_pages
    dtb_pages = page_align(dtb_size, p_size)

    kernel_data = raw[k_offset:k_offset + k_size]
    ramdisk_data = raw[r_offset:r_offset + r_size]
    dtb_data = raw[dtb_offset:dtb_offset + dtb_size]

    return {
        "raw_header": bytearray(hdr),
        "kernel_size": k_size,
        "kernel_addr": k_addr,
        "ramdisk_size": r_size,
        "ramdisk_addr": r_addr,
        "page_size": p_size,
        "header_version": h_ver,
        "dtb_size": dtb_size,
        "dtb_addr": dtb_addr,
        "kernel_data": kernel_data,
        "ramdisk_data": ramdisk_data,
        "dtb_data": dtb_data,
        "cmdline": cmdline,
        "extra_cmdline": extra_cmdline,
        "total_size": len(raw)
    }

def repack_boot(stock_boot_path, new_kernel_path, output_boot_path, target_size=PARTITION_SIZE):
    info = unpack_boot(stock_boot_path)
    
    with open(new_kernel_path, "rb") as f:
        new_kernel = f.read()

    new_k_size = len(new_kernel)
    p_size = info["page_size"]

    print(f"[*] Original Kernel size: {info['kernel_size']} bytes")
    print(f"[*] New Kernel size:      {new_k_size} bytes")
    print(f"[*] Stock Ramdisk size:   {info['ramdisk_size']} bytes")
    print(f"[*] Stock DTB size:       {info['dtb_size']} bytes")

    # Update kernel size in header (offset 8)
    hdr = info["raw_header"]
    struct.pack_into("<I", hdr, 8, new_k_size)

    # Assemble new boot image
    out = bytearray(hdr)

    # Kernel + padding
    out += new_kernel
    k_padding = page_align(new_k_size, p_size) - new_k_size
    out += b"\x00" * k_padding

    # Ramdisk + padding
    out += info["ramdisk_data"]
    r_padding = page_align(info["ramdisk_size"], p_size) - info["ramdisk_size"]
    out += b"\x00" * r_padding

    # DTB + SEANDROIDENFORCE + padding
    dtb_block = info["dtb_data"]
    # Align to 16 bytes before appending signature
    dtb_16_align = (16 - (len(dtb_block) % 16)) % 16
    dtb_block += b"\x00" * dtb_16_align
    dtb_block += SAMSUNG_SEANDROID
    
    out += dtb_block
    dtb_padding = page_align(len(dtb_block), p_size) - len(dtb_block)
    out += b"\x00" * dtb_padding

    # Pad to total partition size
    if len(out) < target_size:
        out += b"\x00" * (target_size - len(out))
    elif len(out) > target_size:
        raise ValueError(f"New boot image exceeds partition size! ({len(out)} > {target_size})")

    with open(output_boot_path, "wb") as f:
        f.write(out)

    print(f"[+] Successfully wrote custom boot image: {output_boot_path} ({len(out)} bytes)")

def main():
    parser = argparse.ArgumentParser(description="Unpack/Repack Android Boot Image v2")
    parser.add_argument("--stock", required=True, help="Path to stock boot.img")
    parser.add_argument("--kernel", required=True, help="Path to new Image.gz")
    parser.add_argument("-o", "--output", required=True, help="Output patched boot.img")
    parser.add_argument("--size", type=int, default=PARTITION_SIZE, help="Target partition size (default: 67108864)")

    args = parser.parse_args()
    repack_boot(args.stock, args.kernel, args.output, args.size)

if __name__ == "__main__":
    main()
