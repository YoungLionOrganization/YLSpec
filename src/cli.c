/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
#define _FILE_OFFSET_BITS 64
#define _POSIX_C_SOURCE 200809L
#include "ylspec.h"
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#define seek64 _fseeki64
#define tell64 _ftelli64
#else
#include <sys/types.h>
#define seek64 fseeko
#define tell64 ftello
#endif
static int reader(void *context, uint64_t offset, void *buffer, size_t size) {
    FILE *f = (FILE *)context;
    if (offset > INT64_MAX || seek64(f, (int64_t)offset, SEEK_SET))
        return -1;
    return fread(buffer, 1, size, f) == size ? 0 : -1;
}
static int error(yl_status s, yl_error *e) {
    fprintf(stderr, "%s: %s (line %zu, column %zu, offset %llu)\n", yl_status_name(s), e->message,
            e->line, e->column, (unsigned long long)e->offset);
    return 1;
}
int main(int argc, char **argv) {
    FILE *f;
    yl_document *d = NULL;
    yl_buffer output = {0};
    yl_error e = {0};
    yl_status s;
    yl_limits l = yl_default_limits();
    char *text;
    size_t n;
    uint64_t offset, available, consumed;
    long long end;
    int result = 0;
    if (argc == 2 && !strcmp(argv[1], "--version")) {
        puts(yl_version());
        return 0;
    }
    if (argc < 3 || argc > 4) {
        fprintf(stderr, "Usage: ylspec validate|inspect|pack DOCUMENT\n       ylspec inspect-frame "
                        "FILE OFFSET\n       ylspec --version\n");
        return 2;
    }
    f = fopen(argv[2], "rb");
    if (!f) {
        perror("Cannot open input");
        return 1;
    }
    if (!strcmp(argv[1], "inspect-frame")) {
        char *tail;
        if (argc != 4 || argv[3][0] == '-') {
            fclose(f);
            return 2;
        }
        errno = 0;
        offset = strtoull(argv[3], &tail, 10);
        if (errno || *tail) {
            fclose(f);
            return 2;
        }
        if (seek64(f, 0, SEEK_END) || (end = (long long)tell64(f)) < 0 || offset > (uint64_t)end) {
            fclose(f);
            return 1;
        }
        available = (uint64_t)end - offset;
        s = yl_read_at(reader, f, offset, available, &l, &d, &consumed, &e);
    } else {
        if (argc != 3 || (strcmp(argv[1], "validate") && strcmp(argv[1], "inspect") &&
                          strcmp(argv[1], "pack"))) {
            fclose(f);
            fprintf(stderr, "Unknown command or extra arguments\n");
            return 2;
        }
        text = (char *)malloc(l.max_document_bytes + 1);
        if (!text) {
            fclose(f);
            return 1;
        }
        n = fread(text, 1, l.max_document_bytes + 1, f);
        if (ferror(f)) {
            free(text);
            fclose(f);
            return 1;
        }
        s = yl_parse(text, n, &l, &d, &e);
        free(text);
    }
    fclose(f);
    if (s)
        return error(s, &e);
    if (!strcmp(argv[1], "validate")) {
        s = yl_validate(d, NULL, &e);
        if (!s)
            puts("Valid YLSpec core.data/0.1 document");
    } else {
        s = !strcmp(argv[1], "pack") ? yl_pack(d, &output, &e) : yl_dump(d, &output, &e);
        if (!s) {
#ifdef _WIN32
            if (!strcmp(argv[1], "pack"))
                _setmode(_fileno(stdout), _O_BINARY);
#endif
            if (fwrite(output.data, 1, output.size, stdout) != output.size)
                result = 1;
        }
    }
    if (s)
        result = error(s, &e);
    yl_buffer_free(&output);
    yl_document_free(d);
    return result;
}
