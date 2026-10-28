/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
#include "bridge.h"
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    const unsigned char *input;
    size_t size, position, capacity, limit;
    yl_buffer output;
    yl_error *error;
    yl_status status;
} codec;
static yl_status problem(codec *c, yl_status status, const char *message) {
    if (!c->status) {
        c->status = status;
        c->error->code = status;
        snprintf(c->error->message, sizeof(c->error->message), "%s", message);
    }
    return c->status;
}
static uint64_t read_number(codec *c, unsigned size) {
    uint64_t value = 0;
    unsigned i;
    if (c->status)
        return 0;
    if (size > c->size - c->position) {
        problem(c, YL_INVALID, "Truncated binding value");
        return 0;
    }
    for (i = 0; i < size; i++)
        value |= (uint64_t)c->input[c->position++] << (8 * i);
    return value;
}
static const unsigned char *read_bytes(codec *c, size_t size) {
    const unsigned char *p;
    if (c->status)
        return NULL;
    if (size > c->size - c->position) {
        problem(c, YL_INVALID, "Truncated binding string");
        return NULL;
    }
    p = c->input + c->position;
    c->position += size;
    return p;
}
static void write_bytes(codec *c, const void *p, size_t size) {
    size_t capacity;
    unsigned char *buffer;
    if (c->status)
        return;
    if (size > c->limit - c->output.size) {
        problem(c, YL_LIMIT, "Binding output limit exceeded");
        return;
    }
    if (c->output.size + size > c->capacity) {
        capacity = c->capacity ? c->capacity : 256;
        while (capacity < c->output.size + size) {
            if (capacity > SIZE_MAX / 2) {
                capacity = c->output.size + size;
                break;
            }
            capacity *= 2;
        }
        buffer = (unsigned char *)realloc(c->output.data, capacity);
        if (!buffer) {
            problem(c, YL_MEMORY, "Cannot allocate binding output");
            return;
        }
        c->output.data = buffer;
        c->capacity = capacity;
    }
    if (size)
        memcpy(c->output.data + c->output.size, p, size);
    c->output.size += size;
}
static void write_number(codec *c, uint64_t number, unsigned size) {
    unsigned char bytes[8];
    unsigned i;
    for (i = 0; i < size; i++)
        bytes[i] = (unsigned char)(number >> (8 * i));
    write_bytes(c, bytes, size);
}
static const char *kinds[] = {"date", "time", "datetime", "datetime-offset"};
static void encode(codec *c, const yl_value *v) {
    size_t i, n;
    uint64_t bits;
    double number;
    const char *text;
    yl_type type = yl_value_type(v);
    write_number(c, type, 1);
    switch (type) {
    case YL_STRING:
    case YL_TEMPORAL:
        if (type == YL_TEMPORAL) {
            for (i = 0; i < 4; i++)
                if (!strcmp(yl_temporal_kind(v), kinds[i]))
                    break;
            write_number(c, i, 1);
        }
        text = yl_value_text(v, &n);
        write_number(c, n, 4);
        write_bytes(c, text, n);
        break;
    case YL_INTEGER:
        write_number(c, (uint64_t)yl_value_integer(v), 8);
        break;
    case YL_FLOAT:
        number = yl_value_float(v);
        memcpy(&bits, &number, 8);
        write_number(c, bits, 8);
        break;
    case YL_BOOLEAN:
        write_number(c, yl_value_boolean(v), 1);
        break;
    case YL_ARRAY:
    case YL_TABLE:
        write_number(c, yl_count(v), 4);
        for (i = 0; i < yl_count(v) && !c->status; i++) {
            if (type == YL_TABLE) {
                text = yl_key(v, i, &n);
                write_number(c, n, 4);
                write_bytes(c, text, n);
            }
            encode(c, yl_at(v, i));
        }
        break;
    }
}
static yl_value *decode(codec *c, unsigned depth, unsigned maximum) {
    yl_value *v = NULL, *child;
    uint64_t bits;
    double number;
    unsigned type, kind;
    size_t i, count, n, key_size;
    const unsigned char *p, *key;
    yl_status s;
    if (c->status)
        return NULL;
    if (depth > maximum) {
        problem(c, YL_LIMIT, "Binding value depth exceeded");
        return NULL;
    }
    type = (unsigned)read_number(c, 1);
    if (c->status)
        return NULL;
    switch (type) {
    case YL_STRING:
        n = (size_t)read_number(c, 4);
        p = read_bytes(c, n);
        if (p)
            v = yl_string((const char *)p, n);
        break;
    case YL_TEMPORAL:
        kind = (unsigned)read_number(c, 1);
        n = (size_t)read_number(c, 4);
        p = read_bytes(c, n);
        if (kind >= 4) {
            problem(c, YL_INVALID, "Invalid binding temporal kind");
            break;
        }
        if (p) {
            v = yl_temporal(kinds[kind], (const char *)p, n);
            if (!v)
                problem(c, YL_INVALID, "Invalid temporal literal");
        }
        break;
    case YL_INTEGER:
        bits = read_number(c, 8);
        {
            int64_t integer;
            memcpy(&integer, &bits, 8);
            v = yl_integer(integer);
        }
        break;
    case YL_FLOAT:
        bits = read_number(c, 8);
        memcpy(&number, &bits, 8);
        v = yl_float(number);
        break;
    case YL_BOOLEAN:
        bits = read_number(c, 1);
        if (bits > 1) {
            problem(c, YL_INVALID, "Invalid binding boolean");
            break;
        }
        v = yl_boolean((int)bits);
        break;
    case YL_ARRAY:
    case YL_TABLE:
        count = (size_t)read_number(c, 4);
        if (count > 16384) {
            problem(c, YL_LIMIT, "Binding container entry limit exceeded");
            break;
        }
        v = yl_new((yl_type)type);
        if (!v)
            break;
        for (i = 0; i < count && !c->status; i++) {
            key = NULL;
            key_size = 0;
            if (type == YL_TABLE) {
                key_size = (size_t)read_number(c, 4);
                key = read_bytes(c, key_size);
                if (!key)
                    break;
                if (yl_get(v, (const char *)key, key_size)) {
                    problem(c, YL_INVALID, "Duplicate binding key");
                    break;
                }
            }
            child = decode(c, depth + 1, maximum);
            if (!child)
                break;
            s = type == YL_TABLE ? yl_set(v, (const char *)key, key_size, child, c->error)
                                 : yl_append(v, child, c->error);
            if (s) {
                c->status = s;
                yl_value_free(child);
                break;
            }
        }
        break;
    default:
        problem(c, YL_INVALID, "Unknown binding value type");
        break;
    }
    if (c->status) {
        yl_value_free(v);
        return NULL;
    }
    if (!v)
        problem(c, YL_MEMORY, "Cannot allocate binding value");
    return v;
}
yl_status yl_bridge_process(int operation, const unsigned char *input, size_t size, size_t offset,
                            const yl_limits *limits, yl_buffer *output, yl_error *error) {
    yl_error local = {0};
    yl_document *document = NULL;
    yl_value *root = NULL;
    yl_limits l = limits ? *limits : yl_default_limits();
    codec c;
    yl_status status = YL_OK;
    if (!error)
        error = &local;
    memset(error, 0, sizeof(*error));
    if (output)
        memset(output, 0, sizeof(*output));
    memset(&c, 0, sizeof(c));
    c.error = error;
    if (!output || (!input && size) || !l.max_document_bytes || !l.max_depth || l.max_depth > 128)
        return problem(&c, YL_INVALID, "Invalid binding arguments");
    c.limit =
        l.max_document_bytes > (SIZE_MAX - 1024) / 8 ? SIZE_MAX : l.max_document_bytes * 8 + 1024;
    if (operation == 0)
        status = yl_parse((const char *)input, size, &l, &document, error);
    else if (operation == 3)
        status = yl_unpack(input, size, offset, &l, &document, NULL, error);
    else if (operation == 1 || operation == 2) {
        if (size > c.limit)
            return problem(&c, YL_LIMIT, "Binding input limit exceeded");
        c.input = input;
        c.size = size;
        root = decode(&c, 0, l.max_depth);
        if (c.status)
            return c.status;
        if (c.position != size) {
            yl_value_free(root);
            return problem(&c, YL_INVALID, "Trailing binding bytes");
        }
        status = yl_document_create(root, &l, &document, error);
        if (status)
            yl_value_free(root);
    } else
        return problem(&c, YL_INVALID, "Unknown binding operation");
    if (status)
        return status;
    if (operation == 1)
        status = yl_dump(document, output, error);
    else if (operation == 2)
        status = yl_pack(document, output, error);
    else {
        encode(&c, yl_root(document));
        status = c.status;
        if (status)
            yl_buffer_free(&c.output);
        else
            *output = c.output;
    }
    yl_document_free(document);
    return status;
}
