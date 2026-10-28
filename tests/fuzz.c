/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
#include "bridge.h"
#include "ylspec.h"
#include <stddef.h>
#include <stdint.h>
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    yl_document *d = NULL;
    yl_error e;
    yl_buffer b = {0};
    yl_limits l = {65536, 32};
    if (yl_parse((const char *)data, size, &l, &d, &e) == YL_OK) {
        yl_dump(d, &b, &e);
        yl_buffer_free(&b);
        yl_pack(d, &b, &e);
        yl_buffer_free(&b);
        yl_document_free(d);
    }
    d = NULL;
    if (yl_unpack(data, size, 0, &l, &d, NULL, &e) == YL_OK)
        yl_document_free(d);
    for (int operation = 1; operation <= 2; operation++) {
        yl_bridge_process(operation, data, size, 0, &l, &b, &e);
        yl_buffer_free(&b);
    }
    return 0;
}
