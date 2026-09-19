# Samsung Galaxy A06 (`SM-A065F`) Custom Recovery Architecture & Porting Guide

Comprehensive guide detailing the engineering architecture, LittleKernel partition geometry constraints, touch release protocol fixes, hardware SAR grip sensor isolation, and Keystore decryption bypass for **TWRP 3.7.1** and **OrangeFox Recovery R12.0** on the **Samsung Galaxy A06 (`SM-A065F`)** (MediaTek Helio G85 MT6769V / Android 14 One UI Core 6.1).

---

## 1. Bootloader Partition Geometry Constraints

The Galaxy A06 LittleKernel (LK) and MediaTek bootloader enforce strict contiguous binary boundaries inside the 85.0 MB (`89,128,960` bytes) `recovery` partition:

| Section | Byte Offset | Size / Boundary | Notes |
| :--- | :--- | :--- | :--- |
| **Android Boot v2 Header** | `0` | `2,048` bytes | Magic `ANDROID!`, OS version, kernel cmdline. |
| **Linux Kernel (Image.gz)** | `2,048` (`0x800`) | `11,804,299` bytes | Padded to 2048-byte page boundary (`11,806,720` / `0xb42800`). |
| **Ramdisk Slot** | `11,806,720` (`0xb42800`) | **Max `31,597,580` bytes (~30.13 MB)** | **Hard ceiling**. Any ramdisk exceeding this bricks boot to Samsung logo. |
| **Device Tree Blob (DTB)** | `43,405,312` (`0x2964800`) | `143,345` bytes | Authentic Samsung MT6768 DTB table. |
| **MediaTek APMCU Debug** | `43,550,720` (`0x2988000`) | `69,632` bytes | LittleKernel hardware table `dbg_apmcu_mp0@0d400000`. |
| **Padding / Zero Fill** | `43,620,352` | Contiguous zeros | Fills up to AVB 2.0 footer. |
| **AVB 2.0 Footer (`AVBf`)** | `89,128,896` | 64 bytes | Validated by LittleKernel AVB verification. |

> [!CAUTION]
> If a recovery ramdisk expands past **`31,597,580` bytes** (e.g. from bundled Magisk zips, addon zips, or uncompressed themes), it will silently overwrite the LittleKernel DTB table and APMCU debug structure at offset `0x2964800`, completely hanging the device at the Samsung Knox logo.

---

## 2. Touch Release Protocol Fix (`libminuitwrp.so`)

### Problem Analysis
In early TWRP and OrangeFox ports on the Galaxy A06, touching any UI element caused the button or slider to stay permanently pressed and highlighted. Swiping failed, sub-menus could not be navigated, and buttons would not fire their release actions.

### Root Cause
1. The **`himax-touchscreen`** Linux kernel driver implements multi-touch Protocol B with a specific release packet sequence:
   - Finger Down: `ABS_MT_TRACKING_ID = <id>`, `ABS_MT_POSITION_X = <x>`, `ABS_MT_POSITION_Y = <y>`, `ABS_MT_TOUCH_MAJOR = <p>`, `ABS_MT_PRESSURE = <p>`.
   - Finger Up: `ABS_MT_TRACKING_ID = -1`, immediately followed in the same event frame by `ABS_MT_TOUCH_MAJOR = 0` (code `48` / `0x30`) and `ABS_MT_PRESSURE = 0` (code `58` / `0x3a`).
2. In `libminuitwrp.so`, the event handler evaluates `ABS_MT_TRACKING_ID = -1` and sets slot `state = 2` (`TOUCH_RELEASE`).
3. However, legacy Protocol A fallback code at `0x229cc` handled `TOUCH_MAJOR = 0` and `PRESSURE = 0` by executing `state = 1` (`TOUCH_HOLD`), directly overwriting `state = 2`.
4. On the subsequent `SYN_REPORT`, `minui` checked if `state == 2`. Because `state` had been clobbered to `1`, no `TOUCH_RELEASE` event was ever emitted to the TWRP/OrangeFox UI engine.

### Binary Jump Table Patch
In `libminuitwrp.so`, the jump table dispatching `EV_ABS` event codes was patched so that codes `48` (`ABS_MT_TOUCH_MAJOR`) and `58` (`ABS_MT_PRESSURE`) jump to the default handler (noop) instead of clobbering slot state:
- **TWRP 3.7.1**: Offsets `0x129b1` and `0x129bb` changed from `0x2a` to `0x02`.
- **OrangeFox R12.0**: Offsets `0x13a91` and `0x13a9b` changed from `0x2c` to `0x02`.

---

## 3. SAR Grip Sensor Hardware Isolation (`clean_inputs.sh`)

The Galaxy A06 features a Semtech SX933x SAR capacitive grip sensor (`smtc_sx933x` at I2C address `5-0028`) that constantly spams input events into `/dev/input/event1`, `event3`, `event4`, `event5`, and `event6`.

To prevent this interrupt spam from saturating the UI poll loop:
1. `clean_inputs.sh` dynamically unbinds the hardware I2C driver:
   ```bash
   echo "5-0028" > /sys/bus/i2c/drivers/smtc_sx933x/unbind 2>/dev/null || true
   ```
2. Unlinks non-touch event nodes (`rm -f /dev/input/event1 ...`).
3. Sets comfortable default screen backlight (`echo 550 > /sys/class/leds/lcd-backlight/brightness`).

---

## 4. OrangeFox Keystore / Metadata Decryption Bypass

### Problem Analysis
When OrangeFox R12.0 booted, it read `/vendor/etc/fstab.mt6768`, identified metadata encryption on `/dev/block/by-name/userdata`, and printed:
```text
Using additional fstab for decryption /etc/additional.fstab
```
It then hung indefinitely on the OrangeFox splash screen.

### Root Cause
OrangeFox called `fscrypt_enable_crypto` -> `retrieveOrGenerateKey()`. Inside `retrieveOrGenerateKey()`, the `Keymaster` module attempted to connect to `android.system.keystore2` via Binder. Because Android system services and Samsung Knox TEEgris RPMB daemons are not running in recovery mode, Binder calls repeatedly returned `-22` (`-EINVAL`). OrangeFox entered a 50-second retry loop with 1-second `nanosleep` intervals, preventing the UI engine from ever starting.

### Binary Patch
In `system/bin/recovery` at function `0x291ff4` (`fscrypt_enable_crypto` metadata handler):
- Original instructions:
  ```arm64
  291ff4: sub sp, sp, #0x140
  291ff8: stp x29, x30, [sp, #224]
  ```
- Patched instructions:
  ```arm64
  291ff4: mov w0, #0    ; Return 0 (failure/skip)
  291ff8: ret           ; Return immediately
  ```
- Hex replacement: `00 00 80 52 c0 03 5f d6`.

With this patch, OrangeFox immediately logs `I:Unable to decrypt metadata encryption` and loads the full GUI pages without delay.

---

## 5. Hardware Backlight Scale Alignment (0–255)

### Problem Analysis
In OrangeFox Recovery, adjusting the brightness slider appeared to do nothing; the screen remained permanently stuck at 100% full illumination.

### Root Cause
1. Galaxy A06 (`SM-A065F`) uses the MediaTek LED driver `/sys/class/leds/lcd-backlight/brightness` with a hardware ceiling of `max_brightness = 255`.
2. The donor recovery binary had hardcoded `tw_brightness_max = 4095` at offset `0xf7080` (`mov w1, #0xfff`), and `vars.xml` set default `tw_brightness_max = 2047`.
3. When the user adjusted the slider from 10% to 100%, the UI calculated brightness values from `409` up to `4095`.
4. Writing any value $\ge 255$ to `/sys/class/leds/lcd-backlight/brightness` was clamped by the Linux kernel LED subsystem to `255`, locking the display at full brightness across the entire slider range.

### Binary & Resource Patch
- **`system/bin/recovery` (Offset `0xf7080`)**:
  - Replaced `5281ffe1` (`mov w1, #0xfff` / 4095) with `52801fe1` (`mov w1, #0xff` / 255).
- **`twres/resources/vars.xml` & `twres/ui.xml`**:
  - Updated `tw_brightness_max` from `2047` to `255`.
  - Configured comfortable default brightness to `120` (~47%).
- **`clean_inputs.sh`**:
  - Sets initial boot brightness to `120` (`echo 120 > /sys/class/leds/lcd-backlight/brightness`).

---

## 6. Timezone UTC Synchronization & Vibrator Deadlock Elimination

### Timezone Real-Time Correction (1-Hour Ahead Fix)
- **Problem**: Recovery displayed the clock 1 hour ahead of true local/UTC time (e.g. `3:16` instead of `2:16`).
- **Root Cause**: `vars.xml` initialized `tw_time_zone="GMT0;BST,M3.5.0,M10.5.0"`. In bionic libc, this rule activated British Summer Time (BST = UTC+1) between March and October.
- **Fix**: Changed `tw_time_zone` and `tw_time_zone_guisel` to pure `UTC0`, and updated `prop.default` (`persist.sys.timezone=UTC`, `ro.timezone=UTC`). Clock matches true real time accurately.

### Vibrator Deadlock Elimination (UI Freeze Fix)
- **Problem**: Toggling the vibration slider in Settings froze the recovery interface completely.
- **Root Cause**: The Galaxy A06 uses an `odm:vibrator@0` hardware motor managed by Samsung's proprietary HAL. In `libminuitwrp.so`, `_Z7vibratei` invoked AIDL `AServiceManager_getService("IVibrator/default")`. Because the AIDL vibrator HAL service is absent in recovery, the Binder IPC call blocked the main UI thread in an unrecoverable kernel sleep.
- **Binary Patch**: In `libminuitwrp.so` at offset `0x24d64` (`_Z7vibratei`), replaced the function prologue with `mov w0, #0; ret` (`00 00 80 52 c0 03 5f d6`). Any vibration call immediately returns 0 without calling Binder, eliminating all freeze risks. `tw_disable_haptics=1` is also set in `vars.xml`.

---

## 7. Pre-Built Flashable Packages

| Package | Size | Target | Flash Slot | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`OrangeFox_R12.0_A06_TouchFixed.tar.md5`** | 89.1 MB | Odin / Odin4 | `AP` | Complete OrangeFox R12.0 with touch release fix, SAR filter, and Keystore bypass. |
| **`TWRP_3.7.1_A06_TouchFixed.tar.md5`** | 89.1 MB | Odin / Odin4 | `AP` | Official TWRP 3.7.1 with touch release jump table patch and SAR filter. |
| **`orangefox_touch_fixed.img`** | 89.1 MB | Heimdall / `dd` | `recovery` | Raw recovery partition image for direct flashing. |
| **`twrp_touch_fixed.img`** | 89.1 MB | Heimdall / `dd` | `recovery` | Raw recovery partition image for direct flashing. |

### Flashing via ADB / Rooted Shell
```bash
adb push work_recovery/orangefox_touch_fixed.img /tmp/recovery.img
adb shell "dd if=/tmp/recovery.img of=/dev/block/by-name/recovery bs=1M && sync && reboot recovery"
```

### Flashing via Odin4 (Linux)
```bash
# Put phone into Download Mode (adb reboot download)
./odin4 -a OrangeFox_R12.0_A06_TouchFixed.tar.md5
```
