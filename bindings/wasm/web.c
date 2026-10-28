/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
#include "bridge.h"
static yl_buffer result;
static yl_error error;
int yl_web_process(int operation, const unsigned char *input, unsigned size, unsigned offset,
                   unsigned maximum, unsigned depth) {
    yl_limits limits = {maximum, depth};
    yl_buffer_free(&result);
    return (int)yl_bridge_process(operation, input, size, offset, &limits, &result, &error);
}
unsigned char *yl_web_data(void) {
    return result.data;
}
unsigned yl_web_size(void) {
    return (unsigned)result.size;
}
const char *yl_web_message(void) {
    return error.message;
}
unsigned yl_web_offset(void) {
    return (unsigned)error.offset;
}
unsigned yl_web_line(void) {
    return (unsigned)error.line;
}
unsigned yl_web_column(void) {
    return (unsigned)error.column;
}
