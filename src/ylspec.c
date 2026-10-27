/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
#include "ylspec.h"
#include "tomlc17.h"
#include <limits.h>
#include <locale.h>
#include <math.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifndef YLSPEC_VERSION
#define YLSPEC_VERSION "0.1.0"
#endif
#define YL_HARD_DEPTH 128u
struct yl_value {
    yl_type type;
    struct yl_value *parent;
    char *text;
    size_t length;
    char kind[24];
    int64_t integer;
    double number;
    int boolean;
    struct yl_value **items;
    char **keys;
    size_t *key_sizes;
    size_t count, capacity;
};
struct yl_document {
    yl_value *root;
    yl_limits limits;
};
static yl_status fail(yl_error *e, yl_status code, const char *fmt, ...) {
    if (e) {
        va_list ap;
        memset(e, 0, sizeof(*e));
        e->code = code;
        va_start(ap, fmt);
        vsnprintf(e->message, sizeof(e->message), fmt, ap);
        va_end(ap);
    }
    return code;
}
static int utf8(const char *s, size_t n, size_t *bad) {
    size_t i = 0;
    while (i < n) {
        unsigned c = (unsigned char)s[i++], cp, need, min;
        if (c < 128)
            continue;
        if (c >= 194 && c <= 223) {
            cp = c & 31;
            need = 1;
            min = 128;
        } else if (c >= 224 && c <= 239) {
            cp = c & 15;
            need = 2;
            min = 2048;
        } else if (c >= 240 && c <= 244) {
            cp = c & 7;
            need = 3;
            min = 65536;
        } else {
            *bad = i - 1;
            return 0;
        }
        if (n - i < need) {
            *bad = i - 1;
            return 0;
        }
        while (need--) {
            c = (unsigned char)s[i++];
            if ((c & 192) != 128) {
                *bad = i - 1;
                return 0;
            }
            cp = (cp << 6) | (c & 63);
        }
        if (cp < min || cp > 0x10ffff || (cp >= 0xd800 && cp <= 0xdfff)) {
            *bad = i - 1;
            return 0;
        }
    }
    return 1;
}
static char *copy(const char *s, size_t n) {
    char *p;
    if (n == SIZE_MAX || (!s && n))
        return NULL;
    p = (char *)malloc(n + 1);
    if (p) {
        if (n)
            memcpy(p, s, n);
        p[n] = 0;
    }
    return p;
}
const char *yl_version(void) {
    return YLSPEC_VERSION;
}
yl_limits yl_default_limits(void) {
    yl_limits l = {16u * 1024u * 1024u, 64};
    return l;
}
const char *yl_status_name(yl_status s) {
    static const char *n[] = {"ok",    "invalid",     "syntax", "limit",  "memory",
                              "frame", "unsupported", "io",     "profile"};
    return (unsigned)s < sizeof(n) / sizeof(*n) ? n[s] : "unknown";
}
void yl_buffer_free(yl_buffer *b) {
    if (b) {
        free(b->data);
        b->data = NULL;
        b->size = 0;
    }
}
yl_value *yl_new(yl_type t) {
    yl_value *v;
    if (t < YL_STRING || t > YL_TABLE)
        return NULL;
    v = (yl_value *)calloc(1, sizeof(*v));
    if (v)
        v->type = t;
    return v;
}
yl_value *yl_string(const char *s, size_t n) {
    yl_value *v = yl_new(YL_STRING);
    if (v) {
        v->text = copy(s, n);
        v->length = n;
        if (!v->text) {
            free(v);
            return NULL;
        }
    }
    return v;
}
yl_value *yl_integer(int64_t n) {
    yl_value *v = yl_new(YL_INTEGER);
    if (v)
        v->integer = n;
    return v;
}
yl_value *yl_float(double n) {
    yl_value *v = yl_new(YL_FLOAT);
    if (v)
        v->number = n;
    return v;
}
yl_value *yl_boolean(int b) {
    yl_value *v = yl_new(YL_BOOLEAN);
    if (v)
        v->boolean = !!b;
    return v;
}
static const char *temporal_kind(toml_type_t t) {
    switch (t) {
    case TOML_DATE:
        return "date";
    case TOML_TIME:
        return "time";
    case TOML_DATETIME:
        return "datetime";
    case TOML_DATETIMETZ:
        return "datetime-offset";
    default:
        return NULL;
    }
}
yl_value *yl_temporal(const char *kind, const char *s, size_t n) {
    yl_value *v;
    toml_result_t r;
    char *source;
    const char *actual;
    size_t i;
    if (!kind || n > 4096 || !s || memchr(s, 0, n))
        return NULL;
    for (i = 0; i < n; i++)
        if (!strchr("0123456789-:+.TtZz ", s[i]))
            return NULL;
    source = (char *)malloc(n + 5);
    if (!source)
        return NULL;
    memcpy(source, "x = ", 4);
    memcpy(source + 4, s, n);
    source[n + 4] = 0;
    r = toml_parse(source, (int)n + 4);
    free(source);
    actual = r.ok ? temporal_kind(toml_get(r.toptab, "x").type) : NULL;
    if (!actual || strcmp(kind, actual) || r.toptab.u.tab.size != 1) {
        toml_free(r);
        return NULL;
    }
    toml_free(r);
    v = yl_string(s, n);
    if (v) {
        v->type = YL_TEMPORAL;
        snprintf(v->kind, sizeof(v->kind), "%s", kind);
    }
    return v;
}
void yl_value_free(yl_value *v) {
    size_t i;
    if (!v || v->parent)
        return;
    for (i = 0; i < v->count; i++) {
        v->items[i]->parent = NULL;
        yl_value_free(v->items[i]);
        if (v->keys)
            free(v->keys[i]);
    }
    free(v->items);
    free(v->keys);
    free(v->key_sizes);
    free(v->text);
    free(v);
}
yl_type yl_value_type(const yl_value *v) {
    return v ? v->type : YL_STRING;
}
const char *yl_value_text(const yl_value *v, size_t *n) {
    if (n)
        *n = v ? v->length : 0;
    return v ? v->text : NULL;
}
const char *yl_temporal_kind(const yl_value *v) {
    return v && v->type == YL_TEMPORAL ? v->kind : NULL;
}
int64_t yl_value_integer(const yl_value *v) {
    return v ? v->integer : 0;
}
double yl_value_float(const yl_value *v) {
    return v ? v->number : 0;
}
int yl_value_boolean(const yl_value *v) {
    return v ? v->boolean : 0;
}
size_t yl_count(const yl_value *v) {
    return v ? v->count : 0;
}
const yl_value *yl_at(const yl_value *v, size_t i) {
    return v && i < v->count ? v->items[i] : NULL;
}
const char *yl_key(const yl_value *v, size_t i, size_t *n) {
    if (n)
        *n = v && v->keys && i < v->count ? v->key_sizes[i] : 0;
    return v && v->keys && i < v->count ? v->keys[i] : NULL;
}
const yl_value *yl_get(const yl_value *v, const char *k, size_t n) {
    size_t i;
    if (!v || v->type != YL_TABLE || (!k && n))
        return NULL;
    for (i = 0; i < v->count; i++)
        if (v->key_sizes[i] == n && (!n || !memcmp(v->keys[i], k, n)))
            return v->items[i];
    return NULL;
}
static int fits(const yl_value *v, size_t depth) {
    size_t i;
    if (depth > YL_HARD_DEPTH)
        return 0;
    for (i = 0; i < v->count; i++)
        if (!fits(v->items[i], depth + 1))
            return 0;
    return 1;
}
static yl_status attach(yl_value *v, const char *k, size_t n, yl_value *child, yl_error *e) {
    size_t i, depth = 0, capacity;
    yl_value *p;
    yl_value **items;
    char **keys = NULL;
    size_t *sizes = NULL;
    char *key = NULL;
    if (!v || !child || child->parent || (v->type != YL_ARRAY && v->type != YL_TABLE) || (!k && n))
        return fail(e, YL_INVALID, "Invalid insertion or already-owned value");
    for (p = v; p; p = p->parent) {
        if (p == child)
            return fail(e, YL_INVALID, "Cyclic value tree");
        if (++depth > YL_HARD_DEPTH)
            return fail(e, YL_LIMIT, "Value tree depth exceeds hard limit");
    }
    if (!fits(child, depth))
        return fail(e, YL_LIMIT, "Value tree depth exceeds hard limit");
    if (v->type == YL_TABLE) {
        size_t bad;
        if (!utf8(k, n, &bad))
            return fail(e, YL_INVALID, "Table key must be UTF-8");
        for (i = 0; i < v->count; i++)
            if (v->key_sizes[i] == n && (!n || !memcmp(v->keys[i], k, n))) {
                v->items[i]->parent = NULL;
                yl_value_free(v->items[i]);
                v->items[i] = child;
                child->parent = v;
                return YL_OK;
            }
        key = copy(k, n);
        if (!key)
            return fail(e, YL_MEMORY, "Cannot allocate key");
    }
    if (v->count >= SIZE_MAX / sizeof(void *) - 1) {
        free(key);
        return fail(e, YL_LIMIT, "Too many values");
    }
    if (v->count < v->capacity) {
        v->items[v->count] = child;
        if (v->keys) {
            v->keys[v->count] = key;
            v->key_sizes[v->count] = n;
        }
        v->count++;
        child->parent = v;
        return YL_OK;
    }
    capacity = v->capacity ? v->capacity * 2 : 8;
    if (capacity < v->count || capacity > SIZE_MAX / sizeof(void *)) {
        free(key);
        return fail(e, YL_LIMIT, "Too many values");
    }
    items = (yl_value **)malloc(capacity * sizeof(*items));
    if (v->type == YL_TABLE) {
        keys = (char **)malloc(capacity * sizeof(*keys));
        sizes = (size_t *)malloc(capacity * sizeof(*sizes));
    }
    if (!items || (v->type == YL_TABLE && (!keys || !sizes))) {
        free(items);
        free(keys);
        free(sizes);
        free(key);
        return fail(e, YL_MEMORY, "Cannot grow value tree");
    }
    if (v->count) {
        memcpy(items, v->items, v->count * sizeof(*items));
        if (keys) {
            memcpy(keys, v->keys, v->count * sizeof(*keys));
            memcpy(sizes, v->key_sizes, v->count * sizeof(*sizes));
        }
    }
    items[v->count] = child;
    if (keys) {
        keys[v->count] = key;
        sizes[v->count] = n;
    }
    free(v->items);
    free(v->keys);
    free(v->key_sizes);
    v->items = items;
    v->keys = keys;
    v->key_sizes = sizes;
    v->capacity = capacity;
    v->count++;
    child->parent = v;
    return YL_OK;
}
yl_status yl_set(yl_value *v, const char *k, size_t n, yl_value *c, yl_error *e) {
    if (!v || v->type != YL_TABLE)
        return fail(e, YL_INVALID, "Expected table");
    return attach(v, k, n, c, e);
}
yl_status yl_append(yl_value *v, yl_value *c, yl_error *e) {
    if (!v || v->type != YL_ARRAY)
        return fail(e, YL_INVALID, "Expected array");
    return attach(v, NULL, 0, c, e);
}
static yl_status check_tree(const yl_value *v, unsigned depth, unsigned limit, yl_error *e) {
    size_t i, bad;
    if (depth > limit)
        return fail(e, YL_LIMIT, "Document nesting limit exceeded");
    if (v->type == YL_STRING && (!v->text || !utf8(v->text, v->length, &bad)))
        return fail(e, YL_INVALID, "Invalid UTF-8 string");
    if (v->type == YL_TEMPORAL && (!v->text || !v->kind[0]))
        return fail(e, YL_INVALID, "Invalid temporal value");
    for (i = 0; i < v->count; i++) {
        yl_status s = check_tree(v->items[i], depth + 1, limit, e);
        if (s)
            return s;
    }
    return YL_OK;
}
static const yl_value *get(const yl_value *v, const char *k) {
    return yl_get(v, k, strlen(k));
}
static int equal_text(const yl_value *v, const char *s) {
    return v && v->type == YL_STRING && v->length == strlen(s) && !memcmp(v->text, s, v->length);
}
static yl_status structure(const yl_value *r, yl_error *e) {
    const yl_value *m, *v, *x;
    size_t i, j;
    if (!r || r->type != YL_TABLE)
        return fail(e, YL_INVALID, "Document root must be a table");
    for (i = 0; i < r->count; i++)
        if (memchr(r->keys[i], 0, r->key_sizes[i]) ||
            (strcmp(r->keys[i], "_ylspec") && strcmp(r->keys[i], "data") &&
             strcmp(r->keys[i], "extensions")))
            return fail(e, YL_INVALID, "Unknown root field");
    m = get(r, "_ylspec");
    if (!m || m->type != YL_TABLE)
        return fail(e, YL_INVALID, "Missing _ylspec table");
    for (i = 0; i < m->count; i++)
        if (memchr(m->keys[i], 0, m->key_sizes[i]) ||
            (strcmp(m->keys[i], "version") && strcmp(m->keys[i], "profile") &&
             strcmp(m->keys[i], "profile_version") && strcmp(m->keys[i], "requires")))
            return fail(e, YL_INVALID, "Unknown _ylspec field");
    if (!equal_text(get(m, "version"), "0.1"))
        return fail(e, YL_UNSUPPORTED, "Unsupported YLSpec version");
    v = get(m, "profile");
    if (!v || v->type != YL_STRING || !v->length || memchr(v->text, 0, v->length))
        return fail(e, YL_INVALID, "Profile must be a nonempty string without NUL");
    v = get(m, "profile_version");
    if (!v || v->type != YL_STRING || !v->length || memchr(v->text, 0, v->length))
        return fail(e, YL_INVALID, "Profile version must be a nonempty string without NUL");
    x = get(r, "data");
    if (!x || x->type != YL_TABLE)
        return fail(e, YL_INVALID, "Missing data table");
    x = get(r, "extensions");
    if (x) {
        if (x->type != YL_TABLE)
            return fail(e, YL_INVALID, "Extensions must be a table");
        for (i = 0; i < x->count; i++) {
            if (x->items[i]->type != YL_TABLE || !x->key_sizes[i] ||
                memchr(x->keys[i], 0, x->key_sizes[i]))
                return fail(e, YL_INVALID, "Extension namespaces must name tables");
        }
    }
    x = get(m, "requires");
    if (x) {
        if (x->type != YL_ARRAY)
            return fail(e, YL_INVALID, "requires must be an array of strings");
        for (j = 0; j < x->count; j++) {
            v = x->items[j];
            if (v->type != YL_STRING || !v->length || memchr(v->text, 0, v->length))
                return fail(e, YL_INVALID,
                            "Required features must be nonempty strings without NUL");
        }
    }
    return YL_OK;
}
yl_status yl_document_create(yl_value *r, const yl_limits *limits, yl_document **out, yl_error *e) {
    yl_limits l = limits ? *limits : yl_default_limits();
    yl_status s;
    yl_document *d;
    if (out)
        *out = NULL;
    if (!out || !r || r->parent)
        return fail(e, YL_INVALID, "Expected unowned root and output pointer");
    if (!l.max_document_bytes || !l.max_depth || l.max_depth > YL_HARD_DEPTH)
        return fail(e, YL_INVALID, "Limits must be positive; maximum supported depth is 128");
    s = check_tree(r, 0, l.max_depth, e);
    if (!s)
        s = structure(r, e);
    if (s)
        return s;
    d = (yl_document *)malloc(sizeof(*d));
    if (!d)
        return fail(e, YL_MEMORY, "Cannot allocate document");
    d->root = r;
    d->limits = l;
    *out = d;
    return YL_OK;
}
static yl_value *convert(toml_datum_t d, const char *source, size_t size, const size_t *lines,
                         size_t line_count, unsigned depth, unsigned max, yl_error *e) {
    yl_value *v = NULL, *child;
    size_t i, n, start, end;
    const char *kind;
    yl_status s;
    if (depth > max) {
        fail(e, YL_LIMIT, "Document nesting limit exceeded");
        return NULL;
    }
    switch (d.type) {
    case TOML_STRING:
        v = yl_string(d.u.str.ptr, (size_t)d.u.str.len);
        break;
    case TOML_INT64:
        v = yl_integer(d.u.int64);
        break;
    case TOML_FP64:
        v = yl_float(d.u.fp64);
        break;
    case TOML_BOOLEAN:
        v = yl_boolean(d.u.boolean);
        break;
    case TOML_DATE:
    case TOML_TIME:
    case TOML_DATETIME:
    case TOML_DATETIMETZ:
        kind = temporal_kind(d.type);
        start = d.lineno > 0 && (size_t)d.lineno <= line_count
                    ? lines[d.lineno - 1] + (size_t)(d.colno - 1)
                    : size;
        end = start;
        while (end < size && strchr("0123456789-:+.TtZz ", source[end]))
            end++;
        while (end > start && source[end - 1] == ' ')
            end--;
        v = yl_string(source + start, end - start);
        if (v) {
            v->type = YL_TEMPORAL;
            snprintf(v->kind, sizeof(v->kind), "%s", kind);
        }
        break;
    case TOML_ARRAY:
    case TOML_TABLE:
        v = yl_new(d.type == TOML_ARRAY ? YL_ARRAY : YL_TABLE);
        if (!v)
            break;
        n = d.type == TOML_ARRAY ? (size_t)d.u.arr.size : (size_t)d.u.tab.size;
        for (i = 0; i < n; i++) {
            child = convert(d.type == TOML_ARRAY ? d.u.arr.elem[i] : d.u.tab.value[i], source, size,
                            lines, line_count, depth + 1, max, e);
            if (!child) {
                yl_value_free(v);
                return NULL;
            }
            s = d.type == TOML_ARRAY ? yl_append(v, child, e)
                                     : yl_set(v, d.u.tab.key[i], (size_t)d.u.tab.len[i], child, e);
            if (s) {
                yl_value_free(child);
                yl_value_free(v);
                return NULL;
            }
        }
        break;
    default:
        fail(e, YL_INVALID, "Unknown TOML value");
        return NULL;
    }
    if (!v)
        fail(e, YL_MEMORY, "Cannot allocate value");
    return v;
}
yl_status yl_parse(const char *text, size_t n, const yl_limits *limits, yl_document **out,
                   yl_error *e) {
    yl_error local_error;
    yl_limits l = limits ? *limits : yl_default_limits();
    size_t i, bad = 0, line_count = 1, *lines;
    toml_result_t result;
    yl_value *root;
    yl_status s;
    if (!e)
        e = &local_error;
    if (e)
        memset(e, 0, sizeof(*e));
    if (out)
        *out = NULL;
    if (!text || !out || !l.max_document_bytes || !l.max_depth || l.max_depth > YL_HARD_DEPTH)
        return fail(e, YL_INVALID, "Invalid parse arguments or limits");
    if (n > l.max_document_bytes || n > INT_MAX)
        return fail(e, YL_LIMIT, "Document byte limit exceeded");
    if (n >= 3 && (unsigned char)text[0] == 0xef && (unsigned char)text[1] == 0xbb &&
        (unsigned char)text[2] == 0xbf)
        return fail(e, YL_SYNTAX, "UTF-8 byte-order mark is not permitted");
    if (!utf8(text, n, &bad) || memchr(text, 0, n)) {
        fail(e, YL_SYNTAX, "Document must be valid UTF-8 without literal NUL bytes");
        if (e)
            e->offset = bad;
        return YL_SYNTAX;
    }
    for (i = 0; i < n; i++)
        if (text[i] == '\n')
            line_count++;
    if (line_count > SIZE_MAX / sizeof(*lines))
        return fail(e, YL_LIMIT, "Too many lines");
    lines = (size_t *)malloc(line_count * sizeof(*lines));
    if (!lines)
        return fail(e, YL_MEMORY, "Cannot allocate source map");
    lines[0] = 0;
    line_count = 1;
    for (i = 0; i < n; i++)
        if (text[i] == '\n')
            lines[line_count++] = i + 1;
    result = toml_parse(text, (int)n);
    if (!result.ok) {
        unsigned long line = 0;
        fail(e, YL_SYNTAX, "%s", result.errmsg);
        if (sscanf(result.errmsg, "(line %lu)", &line) == 1 && line && line <= line_count && e) {
            e->line = (size_t)line;
            e->column = 1;
            e->offset = lines[line - 1];
        }
        toml_free(result);
        free(lines);
        return YL_SYNTAX;
    }
    root = convert(result.toptab, text, n, lines, line_count, 0, l.max_depth, e);
    toml_free(result);
    free(lines);
    if (!root)
        return e ? e->code : YL_MEMORY;
    s = yl_document_create(root, &l, out, e);
    if (s)
        yl_value_free(root);
    return s;
}
const yl_value *yl_root(const yl_document *d) {
    return d ? d->root : NULL;
}
yl_value *yl_root_mutable(yl_document *d) {
    return d ? d->root : NULL;
}
void yl_document_free(yl_document *d) {
    if (d) {
        yl_value_free(d->root);
        free(d);
    }
}
yl_status yl_validate(const yl_document *d, const yl_registry *registry, yl_error *e) {
    const yl_value *m, *p, *v, *required;
    size_t i, j;
    yl_status s;
    if (!d)
        return fail(e, YL_INVALID, "Expected document");
    s = structure(d->root, e);
    if (s)
        return s;
    if (registry && ((registry->count && !registry->profiles) ||
                     (registry->feature_count && !registry->features)))
        return fail(e, YL_INVALID, "Invalid profile registry");
    m = get(d->root, "_ylspec");
    p = get(m, "profile");
    v = get(m, "profile_version");
    required = get(m, "requires");
    if (required)
        for (i = 0; i < required->count; i++) {
            int found = 0;
            for (j = 0; registry && j < registry->feature_count; j++)
                if (equal_text(required->items[i], registry->features[j]))
                    found = 1;
            if (!found)
                return fail(e, YL_UNSUPPORTED, "Required feature is unsupported");
        }
    if (equal_text(p, "core.data") && equal_text(v, "0.1"))
        return YL_OK;
    for (i = 0; registry && i < registry->count; i++) {
        const yl_profile *profile = &registry->profiles[i];
        if (profile->name && profile->version && equal_text(p, profile->name) &&
            equal_text(v, profile->version)) {
            if (!profile->validate)
                return fail(e, YL_PROFILE, "Profile has no validator");
            return profile->validate(d, profile->context, e);
        }
    }
    return fail(e, YL_UNSUPPORTED, "Profile or profile version is unsupported");
}
typedef struct {
    yl_buffer buffer;
    size_t capacity, limit;
    yl_error *error;
    yl_status status;
} writer;
static void emit(writer *w, const char *s, size_t n) {
    size_t cap;
    unsigned char *p;
    if (w->status)
        return;
    if (n > w->limit - w->buffer.size) {
        w->status = fail(w->error, YL_LIMIT, "Serialized document byte limit exceeded");
        return;
    }
    if (w->buffer.size + n + 1 > w->capacity) {
        cap = w->capacity ? w->capacity : 256;
        while (cap < w->buffer.size + n + 1) {
            if (cap > SIZE_MAX / 2) {
                cap = w->buffer.size + n + 1;
                break;
            }
            cap *= 2;
        }
        p = (unsigned char *)realloc(w->buffer.data, cap);
        if (!p) {
            w->status = fail(w->error, YL_MEMORY, "Cannot allocate output");
            return;
        }
        w->buffer.data = p;
        w->capacity = cap;
    }
    if (n)
        memcpy(w->buffer.data + w->buffer.size, s, n);
    w->buffer.size += n;
    w->buffer.data[w->buffer.size] = 0;
}
static void str(writer *w, const char *s) {
    emit(w, s, strlen(s));
}
static void quoted(writer *w, const char *s, size_t n) {
    size_t i;
    char b[8];
    str(w, "\"");
    for (i = 0; i < n; i++) {
        unsigned char c = (unsigned char)s[i];
        if (c == '"' || c == '\\') {
            b[0] = '\\';
            b[1] = (char)c;
            emit(w, b, 2);
        } else if (c < 32 || c == 127) {
            snprintf(b, sizeof(b), "\\u%04X", c);
            str(w, b);
        } else
            emit(w, s + i, 1);
    }
    str(w, "\"");
}
static void serialize(writer *w, const yl_value *v, unsigned depth) {
    size_t i;
    char b[128];
    if (w->status)
        return;
    if (depth > YL_HARD_DEPTH) {
        w->status = fail(w->error, YL_LIMIT, "Serialization depth exceeded");
        return;
    }
    switch (v->type) {
    case YL_STRING:
        quoted(w, v->text, v->length);
        break;
    case YL_TEMPORAL:
        emit(w, v->text, v->length);
        break;
    case YL_INTEGER:
        snprintf(b, sizeof(b), "%lld", (long long)v->integer);
        str(w, b);
        break;
    case YL_FLOAT:
        if (isnan(v->number))
            str(w, "nan");
        else if (isinf(v->number))
            str(w, signbit(v->number) ? "-inf" : "inf");
        else {
            char *p;
            snprintf(b, sizeof(b), "%.17g", v->number);
            p = strchr(b, ',');
            if (p)
                *p = '.';
            str(w, b);
            if (!strchr(b, '.') && !strchr(b, 'e') && !strchr(b, 'E'))
                str(w, ".0");
        }
        break;
    case YL_BOOLEAN:
        str(w, v->boolean ? "true" : "false");
        break;
    case YL_ARRAY:
    case YL_TABLE:
        str(w, v->type == YL_ARRAY ? "[" : "{");
        for (i = 0; i < v->count; i++) {
            if (i)
                str(w, ", ");
            if (v->type == YL_TABLE) {
                quoted(w, v->keys[i], v->key_sizes[i]);
                str(w, " = ");
            }
            serialize(w, v->items[i], depth + 1);
        }
        str(w, v->type == YL_ARRAY ? "]" : "}");
        break;
    }
}
yl_status yl_dump(const yl_document *d, yl_buffer *out, yl_error *e) {
    writer w;
    yl_status s;
    size_t i;
    if (out)
        memset(out, 0, sizeof(*out));
    if (!d || !out)
        return fail(e, YL_INVALID, "Expected document and output");
    s = check_tree(d->root, 0, d->limits.max_depth, e);
    if (!s)
        s = structure(d->root, e);
    if (s)
        return s;
    memset(&w, 0, sizeof(w));
    w.limit = d->limits.max_document_bytes;
    if (w.limit == SIZE_MAX)
        w.limit--;
    w.error = e;
    for (i = 0; i < d->root->count; i++) {
        quoted(&w, d->root->keys[i], d->root->key_sizes[i]);
        str(&w, " = ");
        serialize(&w, d->root->items[i], 1);
        str(&w, "\n");
    }
    if (w.status) {
        yl_buffer_free(&w.buffer);
        return w.status;
    }
    *out = w.buffer;
    return YL_OK;
}
static uint64_t le(const unsigned char *p, unsigned n) {
    uint64_t v = 0;
    unsigned i;
    for (i = 0; i < n; i++)
        v |= (uint64_t)p[i] << (8 * i);
    return v;
}
static void put(unsigned char *p, uint64_t v, unsigned n) {
    unsigned i;
    for (i = 0; i < n; i++)
        p[i] = (unsigned char)(v >> (8 * i));
}
static const unsigned char magic[8] = {'Y', 'L', 'S', 'P', 'E', 'C', 0, 0};
static yl_status header(const unsigned char *p, uint64_t available, yl_limits l, uint64_t *n,
                        yl_error *e) {
    if (memcmp(p, magic, 8))
        return fail(e, YL_FRAME, "Invalid YLSpec magic");
    if (le(p + 8, 2) != 0 || le(p + 10, 2) != 1 || le(p + 12, 4) != 32 || le(p + 24, 4) != 1 ||
        le(p + 28, 4) != 0)
        return fail(e, YL_UNSUPPORTED, "Unsupported frame version, header, encoding, or flags");
    *n = le(p + 16, 8);
    if (*n > l.max_document_bytes || *n > INT_MAX)
        return fail(e, YL_LIMIT, "Embedded document byte limit exceeded");
    if (available < 32 || *n > available - 32)
        return fail(e, YL_FRAME, "Truncated YLSpec frame");
    return YL_OK;
}
yl_status yl_pack(const yl_document *d, yl_buffer *out, yl_error *e) {
    yl_buffer text = {0};
    yl_status s;
    if (out)
        memset(out, 0, sizeof(*out));
    if (!out)
        return fail(e, YL_INVALID, "Expected output");
    s = yl_dump(d, &text, e);
    if (s)
        return s;
    if (text.size > SIZE_MAX - 32) {
        yl_buffer_free(&text);
        return fail(e, YL_LIMIT, "Frame is too large");
    }
    out->data = (unsigned char *)calloc(1, text.size + 32);
    if (!out->data) {
        yl_buffer_free(&text);
        return fail(e, YL_MEMORY, "Cannot allocate frame");
    }
    out->size = text.size + 32;
    memcpy(out->data, magic, 8);
    put(out->data + 10, 1, 2);
    put(out->data + 12, 32, 4);
    put(out->data + 16, text.size, 8);
    put(out->data + 24, 1, 4);
    memcpy(out->data + 32, text.data, text.size);
    yl_buffer_free(&text);
    return YL_OK;
}
yl_status yl_unpack(const void *buffer, size_t size, size_t offset, const yl_limits *limits,
                    yl_document **out, size_t *consumed, yl_error *e) {
    const unsigned char *p = (const unsigned char *)buffer;
    yl_limits l = limits ? *limits : yl_default_limits();
    uint64_t n;
    yl_status s;
    if (out)
        *out = NULL;
    if (consumed)
        *consumed = 0;
    if (!buffer || !out)
        return fail(e, YL_INVALID, "Invalid unpack arguments");
    if (offset > size || size - offset < 32)
        return fail(e, YL_FRAME, "Truncated frame header");
    p += offset;
    s = header(p, size - offset, l, &n, e);
    if (s)
        return s;
    s = yl_parse((const char *)p + 32, (size_t)n, &l, out, e);
    if (!s && consumed)
        *consumed = 32 + (size_t)n;
    return s;
}
yl_status yl_read_at(yl_read_at_fn read, void *context, uint64_t offset, uint64_t available,
                     const yl_limits *limits, yl_document **out, uint64_t *consumed, yl_error *e) {
    unsigned char h[32];
    char *text;
    uint64_t n;
    yl_limits l = limits ? *limits : yl_default_limits();
    yl_status s;
    if (out)
        *out = NULL;
    if (consumed)
        *consumed = 0;
    if (!read || !out)
        return fail(e, YL_INVALID, "Invalid read_at arguments");
    if (available < 32 || offset > UINT64_MAX - available)
        return fail(e, YL_FRAME, "Invalid frame region");
    if (read(context, offset, h, 32))
        return fail(e, YL_IO, "Cannot read frame header");
    s = header(h, available, l, &n, e);
    if (s)
        return s;
    text = (char *)malloc(n ? (size_t)n : 1);
    if (!text)
        return fail(e, YL_MEMORY, "Cannot allocate embedded document");
    if (n && read(context, offset + 32, text, (size_t)n)) {
        free(text);
        return fail(e, YL_IO, "Cannot read embedded document");
    }
    s = yl_parse(text, (size_t)n, &l, out, e);
    free(text);
    if (!s && consumed)
        *consumed = 32 + n;
    return s;
}
