/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
#include "bridge.h"
#include <math.h>
#include <node_api.h>
#include <string.h>
static napi_value invoke(napi_env env, napi_callback_info info) {
    napi_value args[5], result, message, exception, value;
    size_t count = 5, size;
    void *input;
    int32_t operation;
    double offset, maximum, depth;
    bool buffer;
    yl_buffer out = {0};
    yl_error error = {0};
    yl_limits limits;
    if (napi_get_cb_info(env, info, &count, args, NULL, NULL) != napi_ok || count != 5 ||
        napi_get_value_int32(env, args[0], &operation) != napi_ok ||
        napi_is_buffer(env, args[1], &buffer) != napi_ok || !buffer ||
        napi_get_buffer_info(env, args[1], &input, &size) != napi_ok ||
        napi_get_value_double(env, args[2], &offset) != napi_ok ||
        napi_get_value_double(env, args[3], &maximum) != napi_ok ||
        napi_get_value_double(env, args[4], &depth) != napi_ok) {
        napi_throw_type_error(env, NULL,
                              "Expected operation, Buffer, offset, byte limit, and depth");
        return NULL;
    }
    if (!isfinite(offset) || offset < 0 || offset > size || floor(offset) != offset ||
        !isfinite(maximum) || maximum < 1 || maximum > 2147483647 || floor(maximum) != maximum ||
        !isfinite(depth) || depth < 1 || depth > 128 || floor(depth) != depth) {
        napi_throw_range_error(env, NULL, "Invalid offset or resource limits");
        return NULL;
    }
    limits.max_document_bytes = (size_t)maximum;
    limits.max_depth = (unsigned)depth;
    if (yl_bridge_process(operation, (const unsigned char *)input, size, (size_t)offset, &limits,
                          &out, &error)) {
        napi_create_string_utf8(env, error.message, NAPI_AUTO_LENGTH, &message);
        napi_create_error(env, NULL, message, &exception);
        napi_create_string_utf8(env, yl_status_name(error.code), NAPI_AUTO_LENGTH, &value);
        napi_set_named_property(env, exception, "code", value);
        napi_create_double(env, (double)error.offset, &value);
        napi_set_named_property(env, exception, "offset", value);
        napi_create_double(env, (double)error.line, &value);
        napi_set_named_property(env, exception, "line", value);
        napi_create_double(env, (double)error.column, &value);
        napi_set_named_property(env, exception, "column", value);
        napi_throw(env, exception);
        return NULL;
    }
    if (napi_create_buffer_copy(env, out.size, out.data, NULL, &result) != napi_ok) {
        yl_buffer_free(&out);
        napi_throw_error(env, NULL, "Cannot allocate Node result");
        return NULL;
    }
    yl_buffer_free(&out);
    return result;
}
NAPI_MODULE_INIT() {
    napi_value function;
    napi_create_function(env, "process", NAPI_AUTO_LENGTH, invoke, NULL, &function);
    napi_set_named_property(env, exports, "process", function);
    return exports;
}
