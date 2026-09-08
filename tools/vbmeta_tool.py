#!/usr/bin/env python3
"""
vbmeta_tool.py - Standalone Python utility for Samsung / MTK Android Verified Boot (AVB 2.0)
- Generates blank disabled vbmeta images (avbtool equivalent)
- Patches existing stock vbmeta images (flags offset 120-123)
- Packs boot.img and vbmeta.img into Odin-ready .tar archives
"""

import sys
import os
import struct
import tarfile

AVB_MAGIC = b"AVB0"
HEADER_SIZE = 256
DEFAULT_PADDING = 4096

# AVB Flags:
# Bit 0 (1): AVB_VBMETA_IMAGE_FLAGS_HASHTREE_DISABLED (disables dm-verity)
# Bit 1 (2): AVB_VBMETA_IMAGE_FLAGS_DISABLE_VERIFICATION (disables partition signature/hash checks)
FLAG_DISABLE_VERITY = 1
FLAG_DISABLE_VERIFICATION = 2
FLAG_DISABLE_ALL = 3

def create_disabled_vbmeta(output_path="vbmeta_disabled.img", flags=FLAG_DISABLE_VERIFICATION, padding=DEFAULT_PADDING):
    """Generates an official AOSP AVB 2.0 blank disabled vbmeta image."""
    header = bytearray(HEADER_SIZE)
    header[0:4] = AVB_MAGIC
    # Required libavb version 1.2
    header[7] = 1 # major
    header[11] = 2 # minor
    # Offset 120-123 is the 32-bit big-endian flags field
    struct.pack_into(">I", header, 120, flags)
    # Release string
    release = b"avbtool 1.2.0"
    header[128:128+len(release)] = release

    image = bytes(header)
    if len(image) < padding:
        image += b"\x00" * (padding - len(image))

    with open(output_path, "wb") as f:
        f.write(image)

    print(f"[+] Created blank disabled vbmeta: '{output_path}' ({len(image)} bytes, flags=0x{flags:02x})")
    return output_path

def patch_existing_vbmeta(input_path, output_path="vbmeta_patched.img", flags=FLAG_DISABLE_VERIFICATION):
    """Patches verification flags directly in an existing stock vbmeta image."""
    if not os.path.exists(input_path):
        print(f"[-] File not found: {input_path}")
        return False

    with open(input_path, "rb") as f:
        data = bytearray(f.read())

    if data[:4] != AVB_MAGIC:
        print(f"[-] Invalid vbmeta magic. Expected 'AVB0', got {data[:4]}")
        return False

    orig_flags = struct.unpack_from(">I", data, 120)[0]
    struct.pack_into(">I", data, 120, flags)

    with open(output_path, "wb") as f:
        f.write(data)

    print(f"[+] Patched '{input_path}' -> '{output_path}'")
    print(f"    Original flags: 0x{orig_flags:08x} -> New flags: 0x{flags:08x}")
    return output_path

def build_odin_tar(boot_path, vbmeta_path, output_tar="AP_patched.tar"):
    """Packages boot.img and vbmeta.img into a POSIX tarball flashable in Odin AP slot."""
    if not os.path.exists(boot_path):
        print(f"[-] Boot image missing: {boot_path}")
        return False
    if not os.path.exists(vbmeta_path):
        print(f"[-] vbmeta image missing: {vbmeta_path}")
        return False

    with tarfile.open(output_tar, "w") as tar:
        tar.add(boot_path, arcname="boot.img")
        tar.add(vbmeta_path, arcname="vbmeta.img")

    print(f"[+] Successfully built Odin flashable archive: '{output_tar}' ({os.path.getsize(output_tar):,} bytes)")
    return output_tar

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Samsung / MTK AVB 2.0 VBMeta Tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # create
    p_create = subparsers.add_parser("create", help="Create blank disabled vbmeta.img")
    p_create.add_argument("-o", "--output", default="vbmeta_disabled.img", help="Output filename")
    p_create.add_argument("--flags", type=int, default=2, help="Flags: 2 (disable-verification), 3 (disable-all)")

    # patch
    p_patch = subparsers.add_parser("patch", help="Patch flags in existing stock vbmeta.img")
    p_patch.add_argument("input", help="Path to stock vbmeta.img")
    p_patch.add_argument("-o", "--output", default="vbmeta_patched.img", help="Output filename")
    p_patch.add_argument("--flags", type=int, default=2, help="Flags: 2 (disable-verification), 3 (disable-all)")

    # pack
    p_pack = subparsers.add_parser("pack", help="Build Odin flashable AP_patched.tar")
    p_pack.add_argument("--boot", default="boot.img", help="Path to patched boot.img")
    p_pack.add_argument("--vbmeta", default="vbmeta.img", help="Path to disabled/patched vbmeta.img")
    p_pack.add_argument("-o", "--output", default="AP_patched.tar", help="Output tar name")

    args = parser.parse_args()

    if args.command == "create":
        create_disabled_vbmeta(args.output, flags=args.flags)
    elif args.command == "patch":
        patch_existing_vbmeta(args.input, args.output, flags=args.flags)
    elif args.command == "pack":
        build_odin_tar(args.boot, args.vbmeta, args.output)
    else:
        create_disabled_vbmeta("vbmeta_disabled.img")
