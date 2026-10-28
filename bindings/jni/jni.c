/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
#include "bridge.h"
#include <jni.h>
#include <limits.h>
#include <string.h>
static jstring message_string(JNIEnv *env, const char *text) {
    jclass string_class = (*env)->FindClass(env, "java/lang/String");
    if (!string_class)
        return NULL;
    jmethodID constructor =
        (*env)->GetMethodID(env, string_class, "<init>", "([BLjava/lang/String;)V");
    if (!constructor)
        return NULL;
    jbyteArray data = (*env)->NewByteArray(env, (jsize)strlen(text));
    if (!data)
        return NULL;
    (*env)->SetByteArrayRegion(env, data, 0, (jsize)strlen(text), (const jbyte *)text);
    jstring charset = (*env)->NewStringUTF(env, "UTF-8");
    return charset ? (jstring)(*env)->NewObject(env, string_class, constructor, data, charset)
                   : NULL;
}
JNIEXPORT jbyteArray JNICALL Java_io_github_younglionorganization_ylspec_Native_process(
    JNIEnv *env, jclass klass, jint operation, jbyteArray input, jlong offset, jlong maximum,
    jint depth) {
    jbyte *bytes;
    jsize size;
    jbyteArray result;
    yl_buffer output = {0};
    yl_error error = {0};
    yl_limits limits;
    (void)klass;
    if (!input || offset < 0 || maximum < 1 || maximum > INT_MAX || depth < 1 || depth > 128) {
        jclass ex = (*env)->FindClass(env, "java/lang/IllegalArgumentException");
        if (ex)
            (*env)->ThrowNew(env, ex, "Invalid binding input or limits");
        return NULL;
    }
    size = (*env)->GetArrayLength(env, input);
    if ((uint64_t)offset > (uint64_t)size) {
        jclass ex = (*env)->FindClass(env, "java/lang/IllegalArgumentException");
        if (ex)
            (*env)->ThrowNew(env, ex, "Offset exceeds input size");
        return NULL;
    }
    bytes = size ? (*env)->GetByteArrayElements(env, input, NULL) : NULL;
    if (size && !bytes)
        return NULL;
    limits.max_document_bytes = (size_t)maximum;
    limits.max_depth = (unsigned)depth;
    yl_status status = yl_bridge_process(
        operation, size ? (const unsigned char *)bytes : (const unsigned char *)"", (size_t)size,
        (size_t)offset, &limits, &output, &error);
    if (size)
        (*env)->ReleaseByteArrayElements(env, input, bytes, JNI_ABORT);
    if (status) {
        jclass ex =
            (*env)->FindClass(env, "io/github/younglionorganization/ylspec/YLSpecException");
        if (ex) {
            jmethodID ctor = (*env)->GetMethodID(env, ex, "<init>",
                                                 "(Ljava/lang/String;Ljava/lang/String;JJJ)V");
            jstring message = message_string(env, error.message),
                    code = (*env)->NewStringUTF(env, yl_status_name(status));
            if (ctor && message && code) {
                jthrowable instance =
                    (jthrowable)(*env)->NewObject(env, ex, ctor, message, code, (jlong)error.offset,
                                                  (jlong)error.line, (jlong)error.column);
                if (instance)
                    (*env)->Throw(env, instance);
            }
        }
        return NULL;
    }
    if (output.size > INT_MAX) {
        yl_buffer_free(&output);
        jclass ex = (*env)->FindClass(env, "java/lang/OutOfMemoryError");
        if (ex)
            (*env)->ThrowNew(env, ex, "Binding output exceeds Java array limit");
        return NULL;
    }
    result = (*env)->NewByteArray(env, (jsize)output.size);
    if (result)
        (*env)->SetByteArrayRegion(env, result, 0, (jsize)output.size, (const jbyte *)output.data);
    yl_buffer_free(&output);
    return result;
}
