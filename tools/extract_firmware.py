#!/usr/bin/env python3
"""
extract_firmware.py - Fast LZ4 decompressor for Samsung firmware partitions
Uses system liblz4.so.1 via ctypes (no external pip package required).
"""

import sys
import os
import ctypes
import time

def get_lz4_lib():
    for name in ["liblz4.so.1", "liblz4.so", "liblz4.1.dylib", "lz4.dll"]:
        try:
            return ctypes.CDLL(name)
        except OSError:
            continue
    raise RuntimeError("liblz4 library not found on system.")

def decompress_lz4(src_path, dst_path=None, chunk_size=256*1024):
    if not os.path.exists(src_path):
        print(f"[-] Source not found: {src_path}")
        return False

    if dst_path is None:
        if src_path.endswith(".lz4"):
            dst_path = src_path[:-4]
        else:
            dst_path = src_path + ".out"

    liblz4 = get_lz4_lib()
    dctx = ctypes.c_void_p()
    liblz4.LZ4F_createDecompressionContext(ctypes.byref(dctx), 100)

    t0 = time.time()
    total_written = 0

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
                err = liblz4.LZ4F_getErrorName(ret)
                print("[-] Decompression error:", ctypes.string_at(err).decode())
                liblz4.LZ4F_freeDecompressionContext(dctx)
                return False

            if dst_size.value > 0:
                f_out.write(dst_buf.raw[:dst_size.value])
                total_written += dst_size.value

            src_offset += src_chunk_size.value
            if ret == 0:
                break

    liblz4.LZ4F_freeDecompressionContext(dctx)
    elapsed = time.time() - t0
    print(f"[+] Decompressed '{src_path}' -> '{dst_path}'")
    print(f"    Size: {total_written:,} bytes ({total_written / (1024*1024):.1f} MB) in {elapsed:.2f}s")
    return dst_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <partition.img.lz4> [output.img]")
        sys.exit(1)
    out = sys.argv[2] if len(sys.argv) > 2 else None
    decompress_lz4(sys.argv[1], out)
