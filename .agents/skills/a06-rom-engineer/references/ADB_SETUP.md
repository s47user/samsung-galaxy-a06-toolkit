# ADB Setup from Scratch — SM-A065F

Everything needed to get ADB working from a fresh device state.

---

## 1. Enable Developer Options on the Device

```
Settings → About phone → Software information
→ Tap "Build number" exactly 7 times rapidly
→ PIN/Pattern prompt may appear (enter it)
→ Toast: "Developer mode has been enabled"
```

---

## 2. Enable USB Debugging

```
Settings → Developer options → USB debugging → Toggle ON
```

Also enable these for full ROM work:
```
Settings → Developer options → OEM unlocking → Toggle ON  (pre-unlock)
Settings → Developer options → USB debugging (Security settings) → Toggle ON
Settings → Developer options → Wireless debugging → Toggle ON (optional, for Wi-Fi ADB)
```

---

## 3. Connect and Trust the PC

```bash
# On the Linux host:
adb devices
# Device will show: "unauthorized"

# On the phone:
# A dialog appears: "Allow USB debugging?"
# Check: "Always allow from this computer"
# Tap: "Allow"

# Verify on host:
adb devices
# Must show: XXXXXXXX  device  (NOT "unauthorized" or "offline")
```

---

## 4. Verify ADB Shell Works

```bash
adb shell uname -r
# Expected: 4.19.191-29401052-abA065FXXS4AYE2

adb shell getprop ro.product.model
# Expected: SM-A065F

adb shell getprop ro.build.version.release
# Expected: 14

# Test root access (if already rooted):
adb shell "su -c id"
# Expected: uid=0(root) gid=0(root) groups=0(root)
```

---

## 5. Fix Common ADB Connection Issues

### Device shows "unauthorized"
```bash
# Revoke and re-authorize:
adb kill-server
adb start-server
adb devices
# Re-approve on the device when dialog appears
```

### Device not detected at all
```bash
# Check USB connection:
lsusb | grep Samsung
# Expected: ID 04e8:6860 Samsung Electronics Co., Ltd Galaxy A (MTP)

# Check udev rules:
cat /etc/udev/rules.d/51-samsung.rules
# If missing, add: SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", MODE="0666", GROUP="plugdev"
sudo udevadm control --reload-rules && sudo udevadm trigger

# Try different USB mode on device:
# Settings → Developer options → Select USB configuration → MTP or File Transfer
```

### ADB sees device but shell hangs
```bash
# Restart ADB server:
adb kill-server && adb start-server
adb shell

# If still hanging — USB cable issue. Try a different cable.
# Charge-only cables (no data lines) will NOT work with ADB.
```

---

## 6. ADB Over Wi-Fi (Wireless ADB)

Useful for debugging while the phone is connected to a charger, or after Download Mode operations.

```bash
# Method A: Pair via QR code (Android 11+)
# Settings → Developer options → Wireless debugging → Pair device with QR code
adb pair <IP>:<pairing-port>   # Port shown on screen
adb connect <IP>:<adb-port>    # Port shown on screen after pairing

# Method B: Pair via USB first, then switch to Wi-Fi
adb tcpip 5555
adb connect 192.168.X.X:5555   # Replace with device IP
adb disconnect                  # Unplug USB
adb devices                     # Should show device via Wi-Fi

# Find device IP:
adb shell ip route | grep wlan0
# Or: Settings → About phone → Status information → IP address
```

---

## 7. Key ADB Commands for ROM Work

```bash
# File transfer
adb push local_file.img /data/local/tmp/
adb pull /data/local/tmp/output_file .

# Run as root
adb shell "su -c 'dd if=/dev/block/by-name/boot of=/sdcard/boot_dump.img bs=4096'"

# Install APK
adb install KernelSU_Next_v3.3.0.apk
adb install -r --allow-test-apk something.apk   # -r = reinstall

# Sideload OTA or module ZIP in recovery
adb sideload update.zip

# Reboot modes
adb reboot                    # Normal reboot
adb reboot download           # Odin / Download Mode
adb reboot recovery           # Stock Samsung Recovery

# Screen capture
adb shell screencap -p /sdcard/screen.png && adb pull /sdcard/screen.png .

# Screen record (30 sec)
adb shell screenrecord /sdcard/record.mp4 && adb pull /sdcard/record.mp4 .

# Package management
adb shell pm list packages | grep samsung     # List Samsung packages
adb shell pm disable-user --user 0 <pkg>     # Freeze package
adb shell pm enable <pkg>                    # Re-enable package

# Property inspection
adb shell getprop | grep -i "knox\|model\|version\|fingerprint"
```

---

## 8. ADB in Download Mode

ADB does NOT work in Download Mode. Only Heimdall/Odin4 protocol works there.
Use ADB to enter Download Mode, then switch to Heimdall:

```bash
adb reboot download    # Enter Download Mode
heimdall detect        # Verify Download Mode device detected by Heimdall
```

---

## 9. ADB in Stock Recovery

Stock Samsung Recovery has limited ADB access:

```bash
# Enable ADB Sideload from recovery menu:
# Recovery menu → Advanced → ADB Sideload

adb devices   # Should show device in "sideload" mode
adb sideload update.zip
```

Direct shell access in recovery:
```bash
adb shell    # May work in some Samsung recovery versions
ls /dev/block/by-name/    # View partition list
```
