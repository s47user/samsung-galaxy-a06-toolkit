LOCAL_PATH := $(call my-dir)

ifeq ($(TARGET_DEVICE),a06)
include $(call all-subdir-makefiles)
endif
