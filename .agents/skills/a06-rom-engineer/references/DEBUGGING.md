# Debugging Guide — SM-A065F ROM Issues

How to diagnose and read logs when something goes wrong post-flash.

---

## 1. Capture dmesg (Kernel Log)

```bash
# Full kernel log — most useful for boot failures and kernel panics
adb shell dmesg > dmesg_$(date +%Y%m%d_%H%M).txt

# Live streaming dmesg (watch in real time during boot):
adb shell dmesg -w

# Filter for critical errors only:
adb shell dmesg | grep -iE "panic|oops|bug:|error|fail|killed|oom"

# Filter for mount failures (super.img issues):
adb shell dmesg | grep -iE "mount|erofs|ext4|f2fs|dm-"

# Filter for SELinux denials:
adb shell dmesg | grep "avc:"
```

---

## 2. Read a Kernel Panic Stack Trace

A typical kernel panic in dmesg looks like this:

```
[   5.234] Unable to handle kernel paging request at virtual address ffff...
[   5.234] Mem abort info:
[   5.234]   ESR = 0x96000005
[   5.234]   EC = 0x25: DABT (current EL), IL = 32 bits
[   5.234] Call trace:
[   5.234]  futex_wait_queue_me+0x48/0x1c0    ← WHERE it crashed
[   5.234]  futex_wait+0x1c8/0x2dc
[   5.234]  do_futex+0x4dc/0xb20
...
[   5.234] Kernel panic - not syncing: Fatal exception
```

**Reading the trace**:
- First line after "Unable to handle" → the type of fault
- "Call trace" entries → read bottom-to-top = outermost caller first
- If you see `task_struct` offsets + `futex_wait_queue_me` → KABI violation (Rule 5)
- If you see `vmscan` or `mm_` functions → memory subsystem issue (likely MGLRU attempt)
- If you see `selinux_` functions → SELinux policy issue

```bash
# Decode panic addresses with kallsyms (on device with root):
adb shell "su -c 'cat /proc/kallsyms | grep futex_wait_queue_me'"

# Use addr2line on host (requires vmlinux with debug info):
aarch64-linux-gnu-addr2line -e out/vmlinux 0xffffffc01234abcd
```

---

## 3. Capture logcat (Android Log)

```bash
# Full logcat snapshot
adb logcat -d > logcat_$(date +%Y%m%d_%H%M).txt

# Live logcat filtered to crashes only
adb logcat -b crash

# Filter for a specific package (e.g., find why camera fails)
adb logcat | grep -i "SamsungCamera\|CameraService\|HAL"

# Filter for system_server crashes (framework issues)
adb logcat | grep -E "E AndroidRuntime|FATAL EXCEPTION"

# Filter for HAL deaths (after debloating)
adb logcat | grep -iE "hal|hwbinder|died|hidl"

# Useful format: show time + priority + tag + message
adb logcat -v time *:E 2>/dev/null | head -100
```

---

## 4. Diagnose a Debloat-Caused Crash

If Android boots then immediately crashes after a debloat run:

```bash
# Step 1: Get the crash from logcat
adb logcat -b crash -d | head -50

# Step 2: Identify the dying service
adb logcat -d | grep "E System" | head -20
# Look for: "ServiceManager: service 'xxx' died" or ClassNotFoundException

# Step 3: Cross-reference the crashing package against the debloat manifest
# E.g., if crash says com.samsung.android.provider.filterprovider
grep "filterprovider" configs/debloat_manifest.txt
# If found → that package was erroneously removed and must be restored

# Step 4: Restore the super.img with that package present
# (Restore from backup or rebuild super without that package in the manifest)
```

---

## 5. Diagnose a Boot Failure (No ADB Access)

When ADB is unavailable (device not booting far enough):

```bash
# Method 1: Boot into stock recovery, enable ADB sideload, then pull logs
# Power off → Vol Up + Power → Stock Recovery → Advanced → ADB Sideload

# Method 2: Read UART serial output (requires hardware modification — not practical)

# Method 3: Enable early boot logging (add to defconfig):
# CONFIG_PRINTK=y
# CONFIG_LOG_BUF_SHIFT=21
# Then check dmesg immediately after USB connects
adb wait-for-device shell dmesg | head -200
```

---

## 6. Check for SELinux Denials

SELinux denials don't always cause crashes — sometimes they silently break functionality.

```bash
# Check for any denials since last boot
adb shell dmesg | grep "avc: denied"

# More readable format:
adb shell "su -c 'cat /proc/kmsg | grep avc:'"

# Check SELinux enforcement mode:
adb shell getenforce
# Custom kernel should show: Enforcing
# If Permissive: SELinux is disabled — less secure, but useful for debugging

# Temporarily switch to permissive for debugging (requires root):
adb shell "su -c 'setenforce 0'"
# If the crash goes away → it was an SELinux policy denial
# Switch back: adb shell "su -c 'setenforce 1'"
```

---

## 7. Full Bug Report

```bash
# Captures logcat + dmesg + system state in one zip
adb bugreport bugreport_$(date +%Y%m%d).zip

# Extract and read:
unzip bugreport_*.zip -d bugreport_dir/
cat bugreport_dir/dumpstate-board.txt | grep -A20 "KERNEL LOG"
```

---

## 8. Diagnose Boot Partition Issues

```bash
# Check which boot partition is active (A-only device — always boot_a):
adb shell getprop ro.boot.slot_suffix
# Should return: _a (or empty on A-only devices)

# Check AVB verification result:
adb shell dmesg | grep -i "avb\|vbmeta\|verified boot"
# If you see "FAILED" → vbmeta mismatch (Rule 2 violation)

# Confirm SEANDROIDENFORCE was read by init:
adb shell dmesg | grep -i "seandroid"
# Should show: "SELinux: enforcing" shortly after boot
```

---

## 9. Performance Debugging

```bash
# Frame timing — check for jank:
adb shell dumpsys gfxinfo | grep -A5 "Frame Stats"

# CPU frequency in real time:
watch -n1 "adb shell cat /sys/devices/system/cpu/cpufreq/policy6/scaling_cur_freq"

# zRAM compression stats:
adb shell "su -c 'cat /sys/block/zram0/mm_stat'"
# Fields: orig_data_size compr_data_size mem_used_total mem_limit mem_max_used

# Memory pressure check:
adb shell cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree"

# Schedutil response time check:
adb shell cat /sys/devices/system/cpu/cpufreq/policy6/schedutil/up_rate_limit_us
# Should be: 500 (after sysfs tuning)
```

---

## 10. Play Integrity Failure Diagnosis

```bash
# Run diagnostic script
bash scripts/pi_diagnostic.sh

# If DEVICE fails — check which property is wrong:
adb shell "su -c 'cat /data/adb/modules/*/system.prop'" 2>/dev/null
# Compare fingerprint in custom.pif.prop against what the module injects

# Check if Zygisk is active:
adb shell "su -c 'zygisk-ctl status'" 2>/dev/null

# Check module is loaded:
adb shell "su -c 'ksud module list'" 2>/dev/null
# Must show: a06_integrity_shield (or your module name) as enabled

# Manual fingerprint test:
adb shell getprop ro.build.fingerprint
# Must match the passing fingerprint in custom.pif.prop exactly
```
