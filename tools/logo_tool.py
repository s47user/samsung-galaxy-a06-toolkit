#!/usr/bin/env python3
"""
logo_tool.py - Samsung Galaxy A06 (SM-A065F) Boot Logo & Warning Tool
Allows extracting, modifying (custom logo & removing unlocked bootloader warnings),
and repacking up_param.bin for flashing via Odin or dd.
"""

import sys
import os
import tarfile
import argparse
import stat
from PIL import Image

def decompress_lz4_if_needed(src_path, dst_path):
    if src_path.endswith(".lz4"):
        import ctypes
        for name in ["liblz4.so.1", "liblz4.so", "liblz4.1.dylib", "lz4.dll"]:
            try:
                liblz4 = ctypes.CDLL(name)
                break
            except OSError:
                continue
        else:
            raise RuntimeError("liblz4 library not found.")

        dctx = ctypes.c_void_p()
        liblz4.LZ4F_createDecompressionContext(ctypes.byref(dctx), 100)
        chunk_size = 256 * 1024

        with open(src_path, "rb") as f_in, open(dst_path, "wb") as f_out:
            src_buf = f_in.read()
            src_len = len(src_buf)
            src_offset = 0
            dst_buf = ctypes.create_string_buffer(chunk_size)
            dst_size = ctypes.c_size_t(chunk_size)

            while src_offset < src_len:
                src_chunk_size = ctypes.c_size_t(src_len - src_offset)
                dst_size.value = chunk_size
                cur_src = ctypes.byref(ctypes.c_char.from_buffer(bytearray(src_buf[src_offset:])))
                ret = liblz4.LZ4F_decompress(dctx, dst_buf, ctypes.byref(dst_size), cur_src, ctypes.byref(src_chunk_size), None)
                if liblz4.LZ4F_isError(ret):
                    liblz4.LZ4F_freeDecompressionContext(dctx)
                    raise RuntimeError("LZ4 decompression error")
                if dst_size.value > 0:
                    f_out.write(dst_buf.raw[:dst_size.value])
                src_offset += src_chunk_size.value
                if ret == 0:
                    break
        liblz4.LZ4F_freeDecompressionContext(dctx)
        return dst_path
    return src_path

def unpack_up_param(up_param_bin, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with tarfile.open(up_param_bin, "r:") as tar:
        tar.extractall(out_dir)
    # Ensure all extracted files are writable
    for fname in os.listdir(out_dir):
        fpath = os.path.join(out_dir, fname)
        if os.path.isfile(fpath):
            os.chmod(fpath, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    print(f"[+] Successfully extracted {up_param_bin} to {out_dir}/")
    files = sorted(os.listdir(out_dir))
    print(f"    Extracted {len(files)} files: {', '.join(files[:6])} ...")

def suppress_warnings(images_dir, mode="blackout"):
    """
    Suppresses the bootloader unlocked warnings.
    mode="blackout": Replaces warning images with pure black images of exact dimensions (safest, no LK null crashes).
    mode="delete": Deletes the warning files entirely from the archive.
    """
    warning_files = {
        "svb_orange.jpg": (624, 1200),
        "booting_warning.jpg": (624, 292),
        "warning.jpg": (720, 1260),
        "warning_svb.jpg": (720, 1262),
    }

    for fname, size in warning_files.items():
        fpath = os.path.join(images_dir, fname)
        if mode == "delete":
            if os.path.exists(fpath):
                os.remove(fpath)
                print(f"[+] Deleted warning image: {fname}")
        else: # blackout
            if os.path.exists(fpath):
                os.chmod(fpath, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                black_img = Image.new("RGB", size, color=(0, 0, 0))
                black_img.save(fpath, "JPEG", quality=95)
                print(f"[+] Blacked out warning image: {fname} ({size[0]}x{size[1]})")

def set_custom_logo(images_dir, custom_logo_path):
    if not os.path.exists(custom_logo_path):
        raise FileNotFoundError(f"Custom logo image not found: {custom_logo_path}")

    TARGET_RES = (720, 1600)
    with Image.open(custom_logo_path) as img:
        img_rgb = img.convert("RGB")
        if img_rgb.size != TARGET_RES:
            print(f"[*] Resizing custom logo from {img_rgb.size} to {TARGET_RES}...")
            img_rgb = img_rgb.resize(TARGET_RES, Image.Resampling.LANCZOS)
        
        for name in ["logo.jpg", "logo2.jpg"]:
            target_path = os.path.join(images_dir, name)
            if os.path.exists(target_path):
                os.chmod(target_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                img_rgb.save(target_path, "JPEG", quality=95)
                print(f"[+] Updated: {target_path}")

def repack_up_param(images_dir, output_bin, make_odin_tar=True):
    files = sorted(os.listdir(images_dir))
    with tarfile.open(output_bin, "w:", format=tarfile.GNU_FORMAT) as tar:
        for f in files:
            full_path = os.path.join(images_dir, f)
            tar.add(full_path, arcname=f)
    print(f"[+] Repacked {len(files)} files into {output_bin}")

    if make_odin_tar:
        tar_name = output_bin
        if tar_name.endswith(".bin") or tar_name.endswith(".img"):
            tar_name = os.path.splitext(tar_name)[0] + ".tar"
        else:
            tar_name = output_bin + ".tar"

        with tarfile.open(tar_name, "w:", format=tarfile.GNU_FORMAT) as tar:
            tar.add(output_bin, arcname="up_param.bin")
        print(f"[+] Created Odin-flashable archive: {tar_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Samsung Galaxy A06 Boot Logo Customizer")
    subparsers = parser.add_subparsers(dest="command")

    p_unpack = subparsers.add_parser("unpack", help="Unpack up_param.bin")
    p_unpack.add_argument("src", help="Path to up_param.bin or up_param.bin.lz4")
    p_unpack.add_argument("--out", default="up_param_extracted", help="Output directory")

    p_warn = subparsers.add_parser("suppress-warning", help="Black out or delete bootloader unlocked warning")
    p_warn.add_argument("dir", help="Directory of extracted up_param images")
    p_warn.add_argument("--mode", choices=["blackout", "delete"], default="blackout", help="blackout (recommended) or delete")

    p_logo = subparsers.add_parser("set-logo", help="Set custom logo.jpg")
    p_logo.add_argument("dir", help="Directory of extracted up_param images")
    p_logo.add_argument("image", help="Path to custom image (PNG/JPG)")

    p_repack = subparsers.add_parser("repack", help="Repack extracted images into up_param.bin and .tar")
    p_repack.add_argument("dir", help="Directory of extracted up_param images")
    p_repack.add_argument("--out", default="up_param_custom.bin", help="Output bin path")

    args = parser.parse_args()
    if args.command == "unpack":
        tmp_bin = args.src
        if args.src.endswith(".lz4"):
            tmp_bin = args.src[:-4]
            decompress_lz4_if_needed(args.src, tmp_bin)
        unpack_up_param(tmp_bin, args.out)
    elif args.command == "suppress-warning":
        suppress_warnings(args.dir, args.mode)
    elif args.command == "set-logo":
        set_custom_logo(args.dir, args.image)
    elif args.command == "repack":
        repack_up_param(args.dir, args.out)
    else:
        parser.print_help()
