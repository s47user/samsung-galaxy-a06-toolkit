# Anti-Brick Reference — Samsung Galaxy A06 (SM-A065F)
## Complete Brick Prevention, Recovery, and Rescue Guide

This document is the authoritative anti-brick knowledge base for the A06 custom ROM
engineering workflow. Read this entirely before any flash session involving boot, vbmeta,
or bootloader partitions.

---

## 1. Brick Taxonomy — Know What You're Dealing With

Understanding the exact type of failure changes the recovery path completely.

### 1.1 Soft Brick
**Definition**: Android boots to a bootloop, crash, or fails to start UI — but
Download Mode and Stock Recovery are still accessible.

**Symptoms**:
- Phone loops on Samsung logo
- Phone reboots every 10-30 seconds
- System boots but immediately crashes to black
- "Unfortunately System UI has stopped" immediately on boot

**Causes on A06**:
- Custom boot.img paired with wrong/stock vbmeta.img
- Missing SEANDROIDENFORCE footer in repacked boot.img
- Corrupt ramdisk in boot.img
- Bad build.prop property (wrong syntax, missing newline)
- Debloated HAL or system service that was still required

**Recovery path**: Easy — use Download Mode → Heimdall/Odin to reflash stock boot.img.
Download Mode is always accessible on A06 regardless of system state.

---

### 1.2 Semi-Hard Brick
**Definition**: System is stuck — Android will not boot, stock Recovery may not work,
but Download Mode IS still accessible via hardware key combo.

**Symptoms**:
- Only Samsung logo appears and freezes (no bootloop, no progress)
- Screen stays black after power on
- Stock recovery enters but freezes or cannot mount partitions
- "Fail to mount /data" in stock recovery

**Causes on A06**:
- super.img reassembled with wrong partition sizes (lpmake metadata mismatch)
- EROFS filesystem error in system or product partition
- vbmeta_disabled.img corrupted or wrong flags (not 0x02)
- Data partition encryption key mismatch after super.img change without factory reset

**Recovery path**: Medium — Download Mode still works. Use Odin4 to flash full AP
package (super + boot + vbmeta). May also need factory reset from stock recovery after.

---

### 1.3 Hard Brick
**Definition**: Phone is completely unresponsive. Download Mode is NOT accessible.
No response to any key combo. USB is not detected by the host.

**Causes on A06** (These are the absolute forbidden operations):
- Flashing a WRONG BL (bootloader) image — specifically, a BL from a different
  firmware revision or a different variant (SM-A065M BL flashed to SM-A065F).
- Flashing a CP (modem) with mismatched baseband version — can corrupt EFS partition.
- Interrupting a BL or CP flash mid-write (USB disconnect during Odin session).
- Writing zeros or garbage to the `preloader` partition (MTK-specific — destroys
  the first-stage bootloader that activates Download Mode itself).

**Recovery path**: Extremely difficult. May require EDL (Emergency Download Mode)
via MTK BROM (Boot ROM) using SP Flash Tool. Requires physical access to test pads
on the PCB in some cases. Most users cannot self-recover from this state.

**The goal of this entire document is to make hard brick IMPOSSIBLE.**

---

### 1.4 IMEI Brick (Logical Brick)
**Definition**: Phone boots, Android works, but baseband/modem is dead.
IMEI shows as null/invalid. No cellular service. Cannot make calls or use mobile data.

**Causes on A06**:
- EFS partition was wiped or corrupted
- Wrong CP (modem firmware) was flashed
- A debloat script accidentally deleted RIL telephony packages
- Factory reset was performed from a non-Samsung recovery that wiped EFS

**Recovery path**: Restore EFS backup (which is why Rule 12 exists — EFS backup is
mandatory before EVERY flash session). If no EFS backup exists, IMEI recovery
requires sending the device to Samsung service with proof of purchase.

---

## 2. Download Mode — The A06 Lifeline

Download Mode (Odin Protocol) on the A06 is implemented in the Little Kernel (LK)
bootloader and runs BEFORE Android. It is accessible even when:
- Android is completely broken
- system / super partition is corrupt
- boot.img is corrupt or missing
- vbmeta fails verification

**The only way to lose Download Mode access** is a corrupted LK bootloader binary
itself — which is why flashing BL without verified stock firmware is the single most
dangerous operation possible on this device.

### Entering Download Mode
```
Method 1 (Software — from running Android or recovery):
  adb reboot download

Method 2 (Hardware key combo — device completely off):
  1. Power off the device completely (hold Power → Power off)
  2. Hold Volume Up + Volume Down simultaneously
  3. Plug in USB-C cable to PC
  4. Press Volume Up when the blue/teal warning screen appears
  5. Device enters Download Mode — PC detects it as "Samsung Mobile USB Device"

Method 3 (From Download Mode warning screen):
  Press Volume Down to cancel, Volume Up to proceed
```

### Verifying Download Mode on Linux Host
```bash
# Check USB detection:
lsusb | grep Samsung
# Expected: Bus 00X Device 00Y: ID 04e8:685d Samsung Electronics Co., Ltd GALAXY

# Verify Heimdall can see it:
heimdall detect
# Expected: "Device detected"

# If not detected, reload udev rules:
sudo udevadm control --reload-rules && sudo udevadm trigger
```

---

## 3. Stock Recovery Mode

Stock Samsung Recovery is the second safety net after Download Mode.

### Entering Stock Recovery
```
1. Power off the device completely
2. Hold Volume Up + Power button simultaneously
3. Continue holding until Samsung logo appears
4. Release both buttons when you see "Android Recovery" or the Recovery menu

Alternative (from Download Mode):
  Heimdall: heimdall flash --pit a06.pit --boot stock_boot.img
  Then normal reboot → stock recovery becomes accessible again
```

### What Stock Recovery Can Do
- Wipe data / factory reset (DOES NOT touch EFS, BL, modem)
- Apply OTA updates from /sdcard
- Wipe cache partition
- Mount /system for ADB sideload

### What Stock Recovery CANNOT Do
- Flash new firmware (no Odin protocol in recovery)
- Fix a corrupt bootloader
- Recover EFS without a backup
- Fix a mismatched vbmeta (must use Download Mode + Odin for that)

---

## 4. Pre-Flash Ritual — Run This Every Single Time

### Step 1: Verify Device Variant
```bash
# Confirm exact model before ANY flash
adb shell getprop ro.product.model
# Must return: SM-A065F  (or SM-A065M — same hardware, different region)
# NEVER flash SM-A065F firmware to an SM-A065M and vice versa for BL/CP/CSC

adb shell getprop ro.build.version.incremental
# Expected: A065FXXS4AYE2  (confirm you are on the correct firmware base)
```

### Step 2: Backup Critical Partitions
```bash
# EFS (IMEI, network calibration data) — MANDATORY
adb shell "su -c 'dd if=/dev/block/by-name/efs of=/sdcard/efs_backup_$(date +%Y%m%d_%H%M).img bs=4096'"
adb pull /sdcard/efs_backup_$(date +%Y%m%d_%H%M).img .

# Boot partition (always back up before replacing)
adb shell "su -c 'dd if=/dev/block/by-name/boot of=/sdcard/boot_backup_$(date +%Y%m%d).img bs=4096'"
adb pull /sdcard/boot_backup_$(date +%Y%m%d).img .

# vbmeta (to be able to restore stock AVB if needed)
adb shell "su -c 'dd if=/dev/block/by-name/vbmeta of=/sdcard/vbmeta_backup_stock.img bs=4096'"
adb pull /sdcard/vbmeta_backup_stock.img .
```

### Step 3: Checksum Every Artifact Being Flashed
```bash
# Verify against sha256sums.txt
sha256sum -c sha256sums.txt

# Or individually:
sha256sum boot_custom.img
sha256sum vbmeta_disabled.img
sha256sum AP_custom_kernel_AYE2.tar
# Compare output against the known-good values in sha256sums.txt
# DO NOT FLASH if any value differs — the artifact is corrupt
```

### Step 4: Verify boot.img Integrity
```bash
# Check SEANDROIDENFORCE footer (mandatory)
tail -c 17 boot_custom.img | xxd
# Must show: 53 45 41 4e 44 52 4f 49 44 45 4e 46 4f 52 43 45

# Check image size is sane (A06 boot partition = 64 MB)
wc -c boot_custom.img
# Must be exactly: 67108864 bytes (64 * 1024 * 1024)

# Check Android boot magic header
xxd -l 8 boot_custom.img
# Must start: 41 4e 44 52 4f 49 44 21  (ANDROID! magic)
```

### Step 5: Verify vbmeta_disabled.img
```bash
wc -c vbmeta_disabled.img
# Must be: 4096

xxd -l 8 vbmeta_disabled.img
# Must start: 41 56 42 30  (AVB0 magic)

python3 -c "
import struct
d = open('vbmeta_disabled.img', 'rb').read()
flags = struct.unpack('>I', d[120:124])[0]
print(f'AVB flags: 0x{flags:08x}')
# Must print: AVB flags: 0x00000002
"
```

### Step 6: Battery and USB Check
```bash
# Check battery level before flashing
adb shell dumpsys battery | grep level
# Must be above 50 — ideally above 70 for full AP flash

# Verify USB is data-capable (not charge-only)
adb devices
# Must show your device serial number
# If "unauthorized" — approve on device first
```

---

## 5. Brick Trigger Reference — Know Every Landmine

### Landmine 1: vbmeta Mismatch (Most Common Brick Cause)
- **Trigger**: Flashing custom boot.img without simultaneously flashing vbmeta_disabled.img
- **Result**: AVB 2.0 verification failure — red warning screen or bootloop
- **Prevention**: ALWAYS flash boot.img and vbmeta_disabled.img in the SAME Odin session
- **Recovery**: Enter Download Mode → Odin4 with correct vbmeta_disabled.img paired with boot

### Landmine 2: Interrupted Flash Session
- **Trigger**: USB cable disconnect, PC crash, or power cut during Odin/Heimdall write
- **Result**: Partial partition write → corrupted boot or super → soft or semi-hard brick
- **Prevention**:
  - Use a high-quality USB cable (tested for data continuity)
  - Flash from a UPS-backed PC or laptop on battery
  - Never touch USB port during flash — complete hands-off until "PASS" appears in Odin
  - Disable USB selective suspend: `echo on > /sys/bus/usb/devices/usbX/power/control`
- **Recovery**: Re-enter Download Mode, reflash the interrupted partition

### Landmine 3: Wrong Partition Sizes in super.img
- **Trigger**: Rebuilding super.img with lpmake using wrong partition sizes
  (e.g. system partition allocated less space than the actual EROFS image size)
- **Result**: Android cannot mount partitions → kernel panic or mount failure
- **Prevention**:
  - Always use `tools/package_rom.py` which reads the stock A06 lpmake metadata
  - Never manually call `lpmake` without verifying partition size headroom:
    ```bash
    # Check actual EROFS image size vs allocated super slot size
    du -b work_rom/partitions/system_custom.img
    # Must be smaller than the system partition slot size in super metadata
    ```
- **Recovery**: Odin4 with AP_A065F_Debloated_SUPER_ONLY.tar.md5 (known-good super)

### Landmine 4: Removing Critical HAL or RIL Package
- **Trigger**: Adding a system HAL or telephony package to the debloat manifest
- **Result**: Android boots but phone/camera/sensors stop working permanently
- **Prevention**:
  - Always cross-reference debloat manifest against the protected package list
  - Run `--dry-run` and inspect the audit log before any real removal
  - Never remove any `android.hardware.*` or `vendor.mediatek.*` package
- **Recovery**: Full Odin reflash of super (stock or debloated-safe version)

### Landmine 5: Corrupted EFS from Wrong CP Flash
- **Trigger**: Flashing a CP (modem) image from wrong firmware version
- **Result**: IMEI becomes null/000000000000000, no mobile network, "Not registered on network"
- **Prevention**: NEVER flash CP unless you have exact matching stock CP for AYE2
- **Recovery**: Restore EFS backup via:
  ```bash
  # Restore EFS from backup (device must be rooted and running)
  adb push efs_backup_YYYYMMDD.img /data/local/tmp/
  adb shell "su -c 'dd if=/data/local/tmp/efs_backup_YYYYMMDD.img of=/dev/block/by-name/efs bs=4096 && sync'"
  adb reboot
  ```

### Landmine 6: task_struct KABI Violation in Custom Kernel
- **Trigger**: Adding kernel subsystems that change struct task_struct memory layout
  near reserve slots 3-6 (used by MediaTek Task Turbo)
- **Result**: Kernel panic immediately on first context switch (~5 seconds after boot)
- **Prevention**: After any defconfig change that touches mm/sched:
  ```bash
  pahole -C task_struct vmlinux | grep -A10 "__reserved"
  # Compare slot offsets against stock AYE2 vmlinux — must be identical
  ```
- **Recovery**: Boot from stock boot.img (keep boot_backup_pre_ksu.img always available)

### Landmine 7: Bad ro.config.low_ram in build.prop
- **Trigger**: Setting ro.config.low_ram=true in build.prop
- **Result**: Android switches to Go mode — Dalvik heap shrinks, launcher changes,
  3rd party apps may refuse to install ("not compatible with device")
- **Prevention**: Never add this property. Use ro.config.low_ram= check before repacking:
  ```bash
  grep "ro.config.low_ram" /mnt/system_modified/system/build.prop
  # Must return nothing — property must NOT exist
  ```
- **Recovery**: Remove property, rebuild EROFS, rebuild super.img, reflash

### Landmine 8: boot.img Missing SEANDROIDENFORCE
- **Trigger**: Repacking boot.img with a tool that strips the SEANDROIDENFORCE magic footer
- **Result**: SELinux enforcement check fails at early init — system does not start
- **Prevention**: Always verify footer after every repack operation
- **Recovery**: Reflash via Download Mode → Odin4 with correctly repacked boot.img

---

## 6. Emergency Recovery Procedures — Escalation Chain

If something goes wrong, follow this escalation chain in exact order.
**Do not skip steps.** Each step is less destructive than the next.

### Level 1: Soft Brick — Bootloop Recovery
```
Condition: Phone bootloops but Download Mode is accessible.

1. Enter Download Mode (Vol Up + Vol Down + USB, then Vol Up at warning screen)
2. Flash stock boot.img only:
   sudo ./odin4 -a AP_only_stock_boot.tar.md5
   (or: heimdall flash --pit a06.pit --boot stock_boot.img)
3. If boot.img paired with custom vbmeta — also flash vbmeta_disabled.img in same session
4. Reboot normally
5. If still bootlooping → escalate to Level 2
```

### Level 2: Semi-Hard Brick — Full AP Reflash
```
Condition: System completely dead, stock recovery unavailable, Download Mode accessible.

1. Enter Download Mode
2. Flash the full known-good AP package:
   sudo ./odin4 -a AP_A065F_Debloated_SUPER_ONLY.tar.md5
   (This flashes only super.img — safe, zero IMEI/modem risk)
3. If SUPER_ONLY doesn't fix it, flash full AP with kernel + vbmeta:
   sudo ./odin4 -a AP_A065F_Debloated_V1.tar.md5
4. If device doesn't boot after full AP → try factory reset in stock recovery
5. If still dead → escalate to Level 3
```

### Level 3: Full Stock Firmware Restoration
```
Condition: Custom ROM is completely broken. Need to return to 100% stock AYE2.

IMPORTANT: This flashes SUPER + BOOT + VBMETA only (the AP slot).
           BL, CP, CSC are NOT touched — this is intentional and safe.

1. Obtain stock AP from Samsung OSRC or samfrew:
   Firmware: A065FXXS4AYE2 / Region: INS or your local region
   
2. Enter Download Mode

3. Flash stock AP only:
   sudo ./odin4 -a AP_stock_A065FXXS4AYE2.tar.md5
   (Do NOT add -b, -c, or -s arguments)

4. Boot the device — first boot may take 5-8 minutes (dex optimization)

5. If data partition decryption fails:
   Enter Stock Recovery (Vol Up + Power) → Wipe data / Factory reset → Reboot
   
6. Device should now be 100% stock AYE2
```

### Level 4: EFS Restoration (IMEI Lost / No Mobile)
```
Condition: IMEI is null, no mobile network, but device boots.

If you have an EFS backup (you always should after Rule 12):
1. Boot device normally (Wi-Fi/ADB must work)
2. Transfer backup:
   adb push efs_backup_YYYYMMDD.img /data/local/tmp/
3. Flash EFS partition:
   adb shell "su -c 'dd if=/data/local/tmp/efs_backup_YYYYMMDD.img of=/dev/block/by-name/efs bs=4096 && sync'"
4. Reboot device
5. Check IMEI: adb shell "su -c 'cat /data/local/tmp/efs_test || imei'"
   Or dial: *#06# — should display original IMEI

If NO EFS backup exists:
- Samsung service center only. Cannot be recovered in software.
- This is the single most irreversible damage possible. This is why Rule 12 exists.
```

### Level 5: MTK BROM Emergency Recovery (Hard Brick)
```
Condition: Phone is completely dead — no Download Mode, no USB detection, nothing.

IMPORTANT: This is rare and only happens if the LK bootloader was corrupted.
           This should NEVER happen if you follow the golden rules.

Tools Required:
- SP Flash Tool (Linux): https://spflashtools.com/linux
- Stock scatter file for MT6769V (extract from AYE2 firmware)
- A USB Type-A to Type-C cable (some USB-C to C cables don't work with BROM)

Procedure:
1. Power off device completely. Remove battery if possible (not possible on A06 — sealed)
2. Hold Volume Up + Volume Down (both held), then plug USB
3. SP Flash Tool should detect "BROM" mode (MediaTek Boot ROM)
4. In SP Flash Tool: Download → Load Scatter File → Select Format + Download
5. Flash only the preloader and lk partition to recover bootloader
6. Normal Download Mode should then become accessible again

WARNING: SP Flash Tool can destroy all data and is a last resort only.
```

---

## 7. Partition Map — What Each Slot Contains

| Partition Name | Odin Slot | Contents | Safe to Flash? |
|:---|:---:|:---|:---:|
| `boot` | AP | Kernel + ramdisk | YES (with matching vbmeta) |
| `vbmeta` | AP | AVB 2.0 signatures | YES (must be disabled version) |
| `super` | AP | system + product EROFS | YES (primary workflow) |
| `up_param` | BL | Splash/boot logo images | YES (safe, not the bootloader) |
| `preloader` | BL | MTK first-stage bootloader | EXTREME DANGER — never touch |
| `lk` | BL | Little Kernel (Download Mode lives here) | HIGH RISK — only with matching BL |
| `tzsw` | BL | TrustZone secure world | HIGH RISK — do not touch |
| `cp` | CP | Modem / baseband firmware | HIGH RISK — matching AYE2 CP only |
| `efs` | — | IMEI + RF calibration (backed up) | RESTORE ONLY from backup |
| `userdata` | — | User data (encrypted) | Factory reset wipes this safely |
| `cache` | — | System cache | Safe to wipe |
| `odm` | AP (super) | OEM-specific overlays | Inside super — modified via debloat |
| `vendor` | AP (super) | Vendor HALs | Inside super — PROTECTED |

---

## 8. Stock Firmware Sources

For emergency restoration, always obtain firmware from trusted sources:

1. **Samsung OSRC (Open Source Release Center)** — https://opensource.samsung.com/
   - Use for kernel source, not firmware binaries

2. **SamFrew / Frija / Bifrost** (community tools):
   - Frija: https://github.com/SlackingVeteran/frija (Windows GUI)
   - Bifrost: https://github.com/zacharee/SamloaderKotlin (Cross-platform)
   - Region code for SM-A065F: `INS` (India), `BTU` (UK), `EUR` (Europe), etc.
   - Firmware: A065FXXS4AYE2

3. **samfrew.com** — Community-maintained firmware mirrors

**Authentication**: All Samsung firmware is signed and self-verifying. The Odin protocol
verifies the archive MD5 footer before writing. A corrupt download will be rejected by Odin.

---

## 9. Rollback Plan — Always Know Your Exit

Before starting ANY flash session, define and confirm your rollback plan:

```
Flashing custom kernel (boot.img):
  Rollback: Flash boot_backup_pre_ksu.img via Odin/Heimdall
  Location: boot_backup_pre_ksu.img in workspace root
  
Flashing custom super.img:
  Rollback: Flash AP_A065F stock firmware AP slot via Odin4
  Location: ACR-A065FXXS4AYE2-20250519143541/ directory
  
Flashing boot logo (up_param):
  Rollback: Flash up_param_device_backup.bin
  Location: up_param_device_backup.bin in workspace root
  
After EFS backup (Rule 12):
  Rollback: Restore efs_backup_YYYYMMDD.img via dd
  Location: efs_backup_*.img files in workspace root
```

**Rule**: If you cannot immediately answer "how do I undo this?", you are not
ready to flash. Define the rollback first.

---

## 10. Post-Flash Verification Checklist

After every flash session, verify these before considering the work done:

```
[ ] Device boots completely to Android home screen
[ ] Settings → About phone → Build number shows expected firmware/kernel
[ ] Dial *#06# — IMEI is displayed correctly (not null/000000)
[ ] Settings → Mobile networks → shows correct SIM/carrier
[ ] Wi-Fi connects and works
[ ] Camera launches and takes a photo
[ ] Play Store opens (basic connectivity check)
[ ] Root access works: adb shell "su -c id" returns uid=0
[ ] KernelSU Next shows correct kernel version
[ ] bash scripts/pi_diagnostic.sh → BASIC=PASS, DEVICE=PASS
[ ] No unusual heat — device should be room temperature at idle
[ ] Battery percentage is stable (not dropping fast — no power rail issue)
```

If ANY item fails, immediately identify which partition caused it and execute
the appropriate Level 1-4 recovery procedure above.
