# Samsung Galaxy A06 (`SM-A065F`) Experience Suite (v3.0 Final)

A production-grade, systemless KernelSU / Magisk module that unlocks premium Samsung One UI features natively on the **Samsung Galaxy A06 (`SM-A065F` / `SM-A065M`)** running **Android 14 / One UI Core 6.1 (`A065FXXS4AYE2`)**.

This suite also serves as the flagship feature overlay for our **Samsung Galaxy A06 Custom Stock-Based ROM v1.3**.

---

## 1. Feature Overview

| Feature | Scope | Mechanism | Live Verification |
| :--- | :--- | :--- | :--- |
| **Real-Time Network Speed** | Status Bar & Settings | Injected CSC Feature (`CscFeature_Setting_SupportRealTimeNetworkSpeed`) + Global OMC flag | Live upload/download rate dynamically rendered in status bar. |
| **Native 2-Way Hardware Call Recording** | InCallUI & Phone App | CSC Feature (`CscFeature_VoiceCall_ConfigRecording=RecordingAllowed`) | In-call recording button & auto-record menu active in Samsung Phone settings. |
| **Camera Shutter Sound Toggle** | Samsung Camera | ODM project override (`ro.vendor.cam.name=M1`) | Dedicated "Shutter sound" ON/OFF switch in Camera Settings. |
| **Full Samsung Screen Recorder** | SmartCapture & SystemUI | Floating feature flag + QS Tile + overlay permission | 1080p high quality recording, PIP selfie video slider, Quick Settings tile. |
| **System-Wide Dolby Atmos** | SoundAlive & Audio HAL | Floating feature (`AUDIO_SUPPORT_DOLBY_AUDIO`, stereo SoundAlive profiles) | Dolby Atmos tile in Quick Settings and custom equalizer presets. |
| **Smart Call & Spam Protection** | Samsung Contacts & Phone | Hiya anti-malware provider CSC flag (`CscFeature_VoiceCall_SupportCallProtect`) | Caller ID & spam call identification. |
| **Separate App Sound** | AudioService (MultiSound) | Floating feature (`AUDIO_SUPPORT_SEPARATE_APP_SOUND`) | Independent audio routing per application. |
| **High-End UI & Blur Effects** | Launcher & SurfaceFlinger | Floating feature (`LAUNCHER_CONFIG_ANIMATION_TYPE=HighEnd`) | Fluid animations and partial blur. |

---

## 2. Engineering Architecture

Samsung One UI Core stripped or region-locked these features across two distinct config layers:
1. **Encrypted Carrier Configurations (`cscfeature.xml`)**:
   - Located in `/optics` and `/prism` encrypted OMC partitions.
   - At early boot (`post-fs-data`), the module uses a bundled static ARM64 `sec-omc-coder` binary to decrypt the active CSC XML, inject the carrier feature tags, re-encrypt to OMC format, and bind-mount over the read-only partition before Zygote starts.
2. **Device Hardware Capabilities (`floating_feature.xml`)**:
   - Located at `/system/etc/floating_feature.xml`.
   - The module bind-mounts a customized XML enabling `SEC_FLOATING_FEATURE_FRAMEWORK_SUPPORT_SCREEN_RECORDER`, Dolby audio, and animation profiles.
3. **Property Injection (`system.prop`)**:
   - Injects `ro.vendor.cam.name=M1` to bypass Samsung Camera's country-code check for shutter sound menus.
4. **Post-Boot Service (`service.sh`)**:
   - Auto-enables status bar network speed if unset.
   - Adds the Screen Recorder and Dolby tiles to Quick Settings.
   - Grants `SYSTEM_ALERT_WINDOW allow` to `com.samsung.android.app.smartcapture` so the screen recorder overlay functions immediately.

---

## 3. Installation & Verification

### Via KernelSU / Magisk:
1. Transfer `a06_experience_suite.zip` to the device.
2. Open KernelSU-Next or Magisk Manager -> **Modules** -> **Install from storage**.
3. Select `a06_experience_suite.zip`.
4. Reboot the device.

### Verification Commands (ADB Root Shell):
```bash
# Check Screen Recorder service
dumpsys package com.samsung.android.app.smartcapture | grep -i ScreenRecorder

# Check Quick Settings tiles
settings get secure sysui_qs_tiles

# Verify Network Speed status
settings get system network_speed
```
