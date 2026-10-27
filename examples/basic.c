/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
#include "ylspec.h"
#include <stdio.h>
#include <string.h>
int main(void) {
    const char text[] = "[_ylspec]\nversion='0.1'\nprofile='core.data'\nprofile_version='0.1'\n["
                        "data]\nname='Example'\n";
    yl_document *document = NULL, *decoded = NULL;
    yl_buffer frame = {0};
    yl_error error = {0};
    size_t consumed;
    if (yl_parse(text, strlen(text), NULL, &document, &error) != YL_OK)
        goto failed;
    if (yl_validate(document, NULL, &error) != YL_OK)
        goto failed;
    if (yl_pack(document, &frame, &error) != YL_OK)
        goto failed;
    if (yl_unpack(frame.data, frame.size, 0, NULL, &decoded, &consumed, &error) != YL_OK)
        goto failed;
    printf("Decoded %zu bytes with YLSpec %s\n", consumed, yl_version());
    yl_document_free(decoded);
    yl_buffer_free(&frame);
    yl_document_free(document);
    return 0;
failed:
    fprintf(stderr, "%s\n", error.message);
    yl_document_free(decoded);
    yl_buffer_free(&frame);
    yl_document_free(document);
    return 1;
}
