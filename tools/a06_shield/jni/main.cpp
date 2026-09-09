#include <android/log.h>
#include <dlfcn.h>
#include <fcntl.h>
#include <jni.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <sys/system_properties.h>
#include <sys/types.h>
#include <unistd.h>

#include <cstdio>
#include <string>
#include <string_view>
#include <vector>
#include <set>

#include "zygisk.hpp"

#define LOG_TAG "A06_Shield"
#define LOGD(...) __android_log_print(ANDROID_LOG_DEBUG, LOG_TAG, __VA_ARGS__)
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

using zygisk::Api;
using zygisk::AppSpecializeArgs;
using zygisk::ServerSpecializeArgs;

// Types for system property hooking
struct prop_info;
typedef void (*prop_read_callback_fn)(void* cookie, const char* name, const char* value, uint32_t serial);
typedef void (*orig_read_callback_fn)(const prop_info* pi, prop_read_callback_fn callback, void* cookie);
typedef int (*orig_get_fn)(const char* name, char* value);

static orig_read_callback_fn orig_read_callback = nullptr;
static orig_get_fn orig_system_property_get = nullptr;

struct HookCookie {
    prop_read_callback_fn original_callback;
    void* original_cookie;
};

// Check if a property is one of the Samsung Galaxy A06 boot/Knox leak targets
static const char* get_spoofed_prop(const char* name, const char* fallback_value) {
    if (!name) return fallback_value;

    if (strcmp(name, "ro.boot.verifiedbootstate") == 0) {
        return "green";
    } else if (strcmp(name, "ro.boot.flash.locked") == 0) {
        return "1";
    } else if (strcmp(name, "ro.boot.warranty_bit") == 0) {
        return "0";
    } else if (strcmp(name, "ro.boot.vbmeta.device_state") == 0) {
        return "locked";
    } else if (strcmp(name, "sys.oem_unlock_allowed") == 0) {
        return "0";
    } else if (strcmp(name, "ro.is_ever_orange") == 0) {
        return "0";
    } else if (strcmp(name, "ro.boot.em.status") == 0) {
        return "0x0";
    } else if (strcmp(name, "ro.warranty_bit") == 0) {
        return "0";
    } else if (strcmp(name, "ro.build.tags") == 0) {
        return "release-keys";
    } else if (strcmp(name, "ro.build.type") == 0) {
        return "user";
    }

    return fallback_value;
}

static void my_prop_callback(void* cookie, const char* name, const char* value, uint32_t serial) {
    auto* hc = static_cast<HookCookie*>(cookie);
    if (!hc || !hc->original_callback) return;

    const char* spoofed = get_spoofed_prop(name, value);
    hc->original_callback(hc->original_cookie, name, spoofed, serial);
}

static void my_read_callback(const prop_info* pi, prop_read_callback_fn callback, void* cookie) {
    if (!orig_read_callback) return;
    HookCookie hc{callback, cookie};
    orig_read_callback(pi, my_prop_callback, &hc);
}

static int my_get(const char* name, char* value) {
    int ret = orig_system_property_get ? orig_system_property_get(name, value) : 0;
    if (name && value) {
        const char* spoofed = get_spoofed_prop(name, nullptr);
        if (spoofed) {
            strncpy(value, spoofed, PROP_VALUE_MAX - 1);
            value[PROP_VALUE_MAX - 1] = '\0';
            return static_cast<int>(strlen(value));
        }
    }
    return ret;
}

class A06ShieldModule : public zygisk::ModuleBase {
public:
    void onLoad(Api* api, JNIEnv* env) override {
        this->api = api;
        this->env = env;
    }

    void preAppSpecialize(AppSpecializeArgs* args) override {
        if (!args || !args->nice_name) return;

        const char* process_name = env->GetStringUTFChars(args->nice_name, nullptr);
        if (!process_name) return;

        is_target = check_is_target(process_name);
        if (is_target) {
            LOGI("Target detected: %s -> Enabling DenyList unmount", process_name);
            api->setOption(zygisk::Option::FORCE_DENYLIST_UNMOUNT);
        }

        env->ReleaseStringUTFChars(args->nice_name, process_name);
    }

    void postAppSpecialize(const AppSpecializeArgs* /* args */) override {
        if (!is_target) {
            api->setOption(zygisk::Option::DLCLOSE_MODULE_LIBRARY);
            return;
        }

        LOGI("PostAppSpecialize: Sanitizing namespace and hooking properties");

        // Note: umount2 must NOT be called here because SECCOMP is active in postAppSpecialize.
        // Unmounting is handled cleanly by FORCE_DENYLIST_UNMOUNT in preAppSpecialize.

        // Hook system properties in all executable mappings
        hook_properties();
    }

private:
    Api* api = nullptr;
    JNIEnv* env = nullptr;
    bool is_target = false;

    bool check_is_target(const char* name) {
        if (!name) return false;

        // Default targets known to perform bootloader/integrity checks
        static const char* const default_targets[] = {
            "com.google.android.gms",
            "com.google.android.gms.unstable",
            "com.android.vending",
            "gr.nikolasspyr.integritycheck",
            "com.flinkapps.safteynet",
            "com.supercell.brawlstars"
        };

        for (const char* t : default_targets) {
            if (strstr(name, t) != nullptr) {
                return true;
            }
        }

        // Check custom user targets if configured
        FILE* fp = fopen("/data/adb/a06_shield/target.txt", "re");
        if (fp) {
            char line[256];
            while (fgets(line, sizeof(line), fp)) {
                // Strip newline and trailing whitespace
                size_t len = strlen(line);
                while (len > 0 && (line[len - 1] == '\n' || line[len - 1] == '\r' || line[len - 1] == ' ')) {
                    line[--len] = '\0';
                }
                if (len > 0 && line[0] != '#' && strstr(name, line) != nullptr) {
                    fclose(fp);
                    return true;
                }
            }
            fclose(fp);
        }

        return false;
    }

    void hook_properties() {
        FILE* fp = fopen("/proc/self/maps", "re");
        if (!fp) {
            LOGE("Failed to open /proc/self/maps");
            return;
        }

        std::set<std::pair<dev_t, ino_t>> hooked_nodes;
        char line[512];

        while (fgets(line, sizeof(line), fp)) {
            uintptr_t start, end;
            char perms[5];
            unsigned long long offset;
            unsigned int dev_major, dev_minor;
            ino_t inode;
            char path[256] = "";

            if (sscanf(line, "%lx-%lx %4s %llx %x:%x %lu %255s",
                       &start, &end, perms, &offset, &dev_major, &dev_minor, &inode, path) >= 7) {
                // Hook executable mappings of libraries that have an inode
                if (perms[2] == 'x' && inode != 0) {
                    dev_t dev = makedev(dev_major, dev_minor);
                    auto p = std::make_pair(dev, inode);
                    if (hooked_nodes.find(p) == hooked_nodes.end()) {
                        hooked_nodes.insert(p);

                        api->pltHookRegister(dev, inode, "__system_property_read_callback",
                                             reinterpret_cast<void*>(my_read_callback),
                                             reinterpret_cast<void**>(&orig_read_callback));

                        api->pltHookRegister(dev, inode, "__system_property_get",
                                             reinterpret_cast<void*>(my_get),
                                             reinterpret_cast<void**>(&orig_system_property_get));
                    }
                }
            }
        }
        fclose(fp);

        if (api->pltHookCommit()) {
            LOGI("PLT property hooks successfully committed across %zu modules", hooked_nodes.size());
        } else {
            LOGE("Failed to commit PLT property hooks");
        }
    }
};

REGISTER_ZYGISK_MODULE(A06ShieldModule)
