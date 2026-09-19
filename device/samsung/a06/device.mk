LOCAL_PATH := device/samsung/a06

PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/prebuilt/kernel:kernel \
    $(LOCAL_PATH)/prebuilt/dtb.img:dtb.img \
    $(LOCAL_PATH)/recovery/root/init.recovery.mt6768.rc:root/init.recovery.mt6768.rc \
    $(LOCAL_PATH)/recovery/root/init.recovery.samsung.rc:root/init.recovery.samsung.rc \
    $(LOCAL_PATH)/recovery/root/system/etc/recovery.fstab:root/system/etc/recovery.fstab \
    $(LOCAL_PATH)/recovery/root/system/etc/twrp.flags:root/system/etc/twrp.flags
