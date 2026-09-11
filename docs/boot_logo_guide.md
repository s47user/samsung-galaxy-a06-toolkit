# Samsung Galaxy A06 (SM-A065F) Boot Logo & Warning Customization

This guide details how to customize the initial boot splash logo and completely eliminate the Samsung Knox "Bootloader Unlocked" orange warning screen on the Samsung Galaxy A06 (MediaTek Helio G85).

---

## Technical Overview

- **Partition**: `up_param` (`/dev/block/by-name/up_param`).
- **Archive Format**: Standard uncompressed POSIX TAR archive containing JPEG image assets.
- **Bootloader Loader**: MediaTek LittleKernel (`lk-verified.img`).
- **Firmware Location**: Stored as `up_param.bin.lz4` inside the stock `BL_A065F*.tar.md5` package.

### Key Asset Specifications

| File Name | Resolution | Format | Purpose |
| :--- | :--- | :--- | :--- |
| `logo.jpg` | **720 × 1600** | Baseline RGB JPEG | Main boot logo (Samsung Galaxy / Powered by Android) |
| `logo2.jpg` | **720 × 1600** | Baseline RGB JPEG | Secondary boot logo screen |
| `letter.jpg` | **720 × 1600** | Baseline RGB JPEG | Fullscreen splash / letter screen |
| `svb_orange.jpg` | **624 × 1200** | Baseline RGB JPEG | Knox Bootloader Unlocked orange warning banner (Startup) |
| `booting_warning.jpg` | **624 × 292** | Baseline RGB JPEG | "The phone is not running official software" prompt (Startup) |
| `warning.jpg` | **720 × 1260** | Baseline RGB JPEG | Download Mode interactive menu (Volume Up: Continue, Vol Down: Cancel) |
| `warning_svb.jpg` | **720 × 1262** | Baseline RGB JPEG | Download Mode SVB unlock menu (Vol Up long press: Unlock mode) |

---

## Suppressing Bootloader Unlocked Warnings vs Download Mode Screens

- **Normal Startup Warnings (`svb_orange.jpg`, `booting_warning.jpg`)**:
  When the bootloader is unlocked, LittleKernel displays `svb_orange.jpg` and `booting_warning.jpg` for several seconds during normal device boot. These are safely replaced by custom splash branding (e.g. SIAW Freedom logo) or pure black (`#000000`) images to achieve a clean, silent boot.
- **Download Mode Menus (`warning.jpg`, `warning_svb.jpg`)**:
  These screens appear only when intentionally holding `Volume Up + Volume Down` with USB connected. They contain essential interactive button navigation prompts. Keeping them stock ensures you can read the button options clearly without an awkward black box appearing inside the cyan bootloader background.

> [!TIP]
> `tools/logo_tool.py suppress-warning` suppresses startup boot warnings by default while keeping the interactive Download Mode menus intact. If you specifically wish to blackout Download Mode screens as well, pass `--include-download-mode`.

---

## Automated Workflow via `tools/logo_tool.py`

The repository includes [`tools/logo_tool.py`](../tools/logo_tool.py) to automate unpacking, warning suppression, custom logo application, and packaging.

### 1. Extract `up_param`
```bash
python3 tools/logo_tool.py unpack ACR-A065FXXS4AYE2-20250519143541/up_param.bin.lz4 --out boot_logo_extracted/
```

### 2. Suppress Unlocked Warnings (Blackout Mode)
```bash
python3 tools/logo_tool.py suppress-warning boot_logo_extracted/ --mode blackout
```

### 3. Apply Custom Boot Logo
Any PNG or JPG will be automatically formatted and resized to 720x1600:
```bash
python3 tools/logo_tool.py set-logo boot_logo_extracted/ custom_logo_siaw.png
```

### 4. Repack for Odin or Direct Root Flashing
```bash
python3 tools/logo_tool.py repack boot_logo_extracted/ --out up_param_custom.bin
```
This produces:
- `up_param_custom.bin`: Raw partition image for `dd`.
- `up_param_custom.tar`: Flashable in Odin.

---

## Flashing Instructions

### Method A: Odin (Download Mode — No Root Required)
1. Boot the phone into **Download Mode** (Hold Volume Up + Volume Down while plugging in USB cable connected to PC).
2. Open Odin (or `odin4` on Linux).
3. Place `up_param_custom.tar` in the **BL** slot.
4. Click **Start**.

### Method B: Direct Write via Root / Termux / ADB (Device Running)
If rooted via APatch or Magisk:
```bash
adb push up_param_custom.bin /sdcard/
adb shell
su
dd if=/sdcard/up_param_custom.bin of=/dev/block/by-name/up_param
reboot
```
