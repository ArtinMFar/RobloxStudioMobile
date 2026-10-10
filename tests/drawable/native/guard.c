// Test helper: a direct buffer that ends exactly at an inaccessible (PROT_NONE) page, so any
// read or write past its end faults with SIGSEGV / SEGV_ACCERR like on the phone.
#include <jni.h>
#include <sys/mman.h>
#include <unistd.h>

JNIEXPORT jobject JNICALL
Java_com_winlator_xserver_DrawableTest_guardedBuffer(JNIEnv *env, jclass cls, jint size) {
    long page = sysconf(_SC_PAGESIZE);
    long len = ((size + page - 1) / page) * page;
    char *base = mmap(NULL, len + page, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (base == MAP_FAILED) return NULL;
    mprotect(base + len, page, PROT_NONE);
    return (*env)->NewDirectByteBuffer(env, base + (len - size), size);
}
