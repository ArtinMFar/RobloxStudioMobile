#include <jni.h>
#include <stdint.h>
typedef struct { uint32_t width, height, stride; int32_t format; uint32_t flags; } AndroidBitmapInfo;
static inline int AndroidBitmap_getInfo(JNIEnv* e, jobject b, AndroidBitmapInfo* i) { return -1; }
static inline int AndroidBitmap_lockPixels(JNIEnv* e, jobject b, void** p) { return -1; }
static inline int AndroidBitmap_unlockPixels(JNIEnv* e, jobject b) { return 0; }
