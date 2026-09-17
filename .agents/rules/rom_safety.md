---
trigger: always_on
---

# Samsung Galaxy A06 — ROM Development Safety Protocol

This workspace is the **Samsung Galaxy A06 (SM-A065F)** custom ROM toolkit.
All interactions in this workspace are subject to the following mandatory rules.

## Device Context
- **Device**: SM-A065F / SM-A065M
- **SoC**: MediaTek Helio G85 (MT6769V/CZ)
- **Firmware**: A065FXXS4AYE2 (Android 14 / One UI Core 6.1)
- **Kernel**: Linux 4.19.191 Non-GKI

## Hard Constraints — Refuse Any Request That Would Violate These

1. **Never suggest CPU/GPU overclocking** — silicon-binned MTK G85, no heat pipe, guaranteed instability.
2. **Never suggest MGLRU backport to 4.19** — causes kernel panics in mm/vmscan.c on MTK vendor tree.
3. **Never suggest flashing CP/BL/CSC** unless the user explicitly has verified matching stock firmware.
4. **Never suggest ro.config.low_ram** — triggers Android Go mode on a 4 GB device.
5. **Always require EFS backup** before any flash session guidance.
6. **Always verify SEANDROIDENFORCE footer** in any boot.img before flashing.
7. **Always pair custom boot.img with vbmeta_disabled.img** in the same flash session.
8. **Never suggest removing protected hardware packages** (SamsungCamera, sileadManager, HALs, telephony stack).
9. **Never remove CMHProvider without isolated test gating** — protects SecGallery from content provider null pointers.
10. **Never remove SmartSwitchStub when SecSetupWizard_Global is present** — prevents first-boot setup wizard crash loops.
11. **Never touch vendor hardware integration daemons** (e.g., sileadManager for biometric/touch IC).

## Engineering Rigor & Systems Protocol

1. **Strict Dependency & Orphan Auditing**:
   - Never classify an APK or service from package names alone. Trace ContentProvider authorities, intent filters, AIDL interfaces, bound services, and settings search indexers.
   - When a parent service is removed, immediately identify and clean or evaluate all downstream orphans (e.g. Fmm, SmartCallProvider, PrivateComputeServices, ThemeStore, SamsungMultiConnectivity).
   - Explicitly flag feature regressions (e.g. SecAppSeparation removing Dual Messenger).

2. **Accurate Systems Accounting**:
   - Never equate RSS to reclaimed physical RAM. Distinguish clean/evictable file-backed pages and shared Zygote libraries from anonymous dirty pages (PSS). Realistically estimate 60–90 MB PSS headroom gains on 4 GB targets.
   - Account for EROFS block compression (LZ4/ZSTD) when projecting partition size deltas.

3. **Build & Filesystem Integrity**:
   - Preserve SELinux file_contexts and fs_config capabilities across all EROFS extractions and repacks.
   - Always verify RMM/KG state is 'Checking' or 'Normal' (never 'Prenormal') before flashing.
   - Pair any modified super.img / boot.img with vbmeta_disabled.img (flags=0x02).

4. **Staged Sequencing & Logcat Diagnostics**:
   - Never perform multi-variable shotgun flashes. Stage removals: Group A (dead code) -> Group B (performance) -> Isolated single-package tests (CMHProvider).
   - Require post-boot empirical verification:
     `adb logcat -b all | grep -iE "FATAL|ANR|ClassNotFound|ActivityNotFound"`
   - Always retain pristine, untouched extracted filesystem trees for immediate surgical rollback.

## Agent Behavior
- For ANY ROM task, read and follow `.agents/skills/a06-rom-engineer/SKILL.md` completely.
- Always run sha256sum before suggesting any flash operation.
- For kernel builds, always verify task_struct KABI reserve slots 3-6 are preserved.
- Default to the SUPER_ONLY flash path (AP_A065F_Debloated_SUPER_ONLY.tar.md5) unless
  the user explicitly needs to update the kernel or vbmeta.

