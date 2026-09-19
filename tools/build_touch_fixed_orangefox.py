#!/usr/bin/env python3
"""
build_touch_fixed_orangefox.py
Constructs the Odin-flashable OrangeFox Recovery R12.0 tar.md5 for Samsung Galaxy A06 (SM-A065F).
Features:
  1. OrangeFox Recovery R12.0 core engine with full UI, themes, and tools.
  2. Patched libminuitwrp.so jump table (preventing TOUCH_MAJOR/PRESSURE=0 clobbering release state).
  3. Dynamic clean_inputs.sh unbinding hardware SAR grip sensor (5-0028).
  4. Precise 31,597,580-byte slot geometry preserving MediaTek APMCU table, DTB, and AVB 2.0 footer.
"""

import os
import subprocess
import gzip
import tarfile
import hashlib

WORKSPACE = "/home/lenovo/ROM AND CUSTOM OS PORTING"
RAMDISK_DIR = os.path.join(WORKSPACE, "work_recovery/orangefox_a06_staging/ramdisk")
OFFICIAL_IMG = os.path.join(WORKSPACE, "work_recovery/twrp_official_a06.img")
OUTPUT_IMG = os.path.join(WORKSPACE, "work_recovery/orangefox_touch_fixed.img")
OUTPUT_TAR = os.path.join(WORKSPACE, "OrangeFox_R12.0_A06_TouchFixed.tar.md5")

SLOT_SIZE = 31597580
OFFSET = 11806720

def main():
    print("[*] Repacking OrangeFox ramdisk...")
    find_cmd = "find . -mindepth 1 -printf \"%P\\n\" | LC_ALL=C sort | cpio -o -H newc -R 0:0"
    proc = subprocess.Popen(find_cmd, shell=True, cwd=RAMDISK_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cpio_data, err = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(err)

    print(f"[+] CPIO archive: {len(cpio_data):,} bytes")
    gz_data = gzip.compress(cpio_data, compresslevel=9, mtime=0)
    print(f"[+] Gzip stream:  {len(gz_data):,} bytes")

    if len(gz_data) > SLOT_SIZE:
        raise ValueError(f"Ramdisk exceeds allocated slot size: {len(gz_data)} > {SLOT_SIZE}")

    padding = SLOT_SIZE - len(gz_data)
    ramdisk_block = gz_data + b"\x00" * padding

    with open(OFFICIAL_IMG, "rb") as f:
        full_image = bytearray(f.read())

    full_image[OFFSET:OFFSET + SLOT_SIZE] = ramdisk_block

    with open(OUTPUT_IMG, "wb") as f:
        f.write(full_image)
    print(f"[+] Spliced OrangeFox recovery image: {OUTPUT_IMG} ({len(full_image):,} bytes)")

    print("[*] Packaging into tar.md5...")
    tar_tmp = "/tmp/orangefox_touch_fixed.tar"
    with tarfile.open(tar_tmp, "w") as tar:
        tar.add(OUTPUT_IMG, arcname="recovery.img")

    with open(tar_tmp, "rb") as f:
        tar_content = f.read()

    md5 = hashlib.md5(tar_content).hexdigest()
    with open(OUTPUT_TAR, "wb") as f:
        f.write(tar_content)
        f.write(f"{md5}  recovery.img\n".encode("ascii"))

    print(f"[+] Successfully built: {OUTPUT_TAR} ({os.path.getsize(OUTPUT_TAR):,} bytes)")
    print(f"    MD5: {md5}")

if __name__ == "__main__":
    main()
