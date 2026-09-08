# Performance Tuning & Stutter Fixes for Galaxy A06 (Helio G85)

## The Core Bottleneck: eMMC 5.1 & RAM Plus
The Galaxy A06 uses budget **eMMC 5.1 storage** (~200MB/s sequential, very slow random 4K read/write).
By default, Samsung enables **RAM Plus**, which swaps inactive RAM pages to a swapfile located on the eMMC flash memory. 

When multitasking or switching apps, the CPU freezes waiting for flash storage I/O, causing severe micro-stutter and frame drops.

---

## 1. Disable Samsung RAM Plus
Turn off Samsung's flash swap immediately:
- **Via Settings**: *Settings -> Device Care -> Memory -> RAM Plus -> Toggle OFF* -> Restart.
- **Via ADB / Root Shell**:
  ```bash
  adb shell settings put global ram_expand_size 0
  ```

---

## 2. In-RAM zRAM Configuration (LZ4 / ZSTD)
Instead of disk swap, keep swap compressed inside physical RAM using **SmartPack Kernel Manager** or a zRAM Magisk/APatch module:
- **Algorithm**: `lz4` (fastest) or `zstd` (highest compression ratio).
- **Size**: 2048 MB (50% of physical RAM).
- **Swappiness**: Set to `100` (instructs the kernel to aggressively compress inactive pages into zRAM rather than dropping disk caches).
- **Page-cluster**: `0` (reads one page at a time, lowering memory latency).

---

## 3. CPU Schedutil Governor Tuning
The Helio G85 has 2x Cortex-A75 (big) cores and 6x Cortex-A55 (LITTLE) cores. Samsung's stock schedutil governor ramps up frequencies conservatively.

Inside SmartPack Kernel Manager (or an init script):
```bash
# Reduce big core ramp-up delay from 1000us to 500us
echo 500 > /sys/devices/system/cpu/cpufreq/policy6/schedutil/up_rate_limit_us
echo 20000 > /sys/devices/system/cpu/cpufreq/policy6/schedutil/down_rate_limit_us

# LITTLE cores
echo 1000 > /sys/devices/system/cpu/cpufreq/policy0/schedutil/up_rate_limit_us
```

---

## 4. Storage I/O Read-Ahead Optimization
Increase block device read-ahead buffer from default `128 KB` to `512 KB` to speed up media loading:
```bash
for queue in /sys/block/mmcblk0*/queue/read_ahead_kb; do
    echo 512 > "$queue"
done
```

---

## 5. Safe Debloat (Freeze, Never Uninstall)
Never delete core system APKs via `pm uninstall` on One UI Core, as framework dependencies can crash `system_server`. Freeze them instead using Hail, Shizuku, or shell:

```bash
# Safe to disable:
pm disable-user --user 0 com.samsung.android.bixby.agent
pm disable-user --user 0 com.samsung.android.spage          # Samsung Free
pm disable-user --user 0 com.sec.android.app.sbrowser      # Samsung Internet
pm disable-user --user 0 com.samsung.android.mdx           # Link to Windows
pm disable-user --user 0 com.samsung.android.rubin.app     # Customization / Telemetry
```
