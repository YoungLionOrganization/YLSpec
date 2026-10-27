/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
#ifndef YLSPEC_H
#define YLSPEC_H
#include <stddef.h>
#include <stdint.h>
#ifdef _WIN32
# if defined(YLSPEC_SHARED)
#  if defined(YLSPEC_BUILD)
#   define YL_API __declspec(dllexport)
#  else
#   define YL_API __declspec(dllimport)
#  endif
# else
#  define YL_API
# endif
#else
# define YL_API __attribute__((visibility("default")))
#endif
#ifdef __cplusplus
extern "C" {
#endif
typedef enum { YL_OK, YL_INVALID, YL_SYNTAX, YL_LIMIT, YL_MEMORY, YL_FRAME,
               YL_UNSUPPORTED, YL_IO, YL_PROFILE } yl_status;
typedef enum { YL_STRING, YL_INTEGER, YL_FLOAT, YL_BOOLEAN, YL_TEMPORAL,
               YL_ARRAY, YL_TABLE } yl_type;
typedef struct { yl_status code; uint64_t offset; size_t line, column; char message[256]; } yl_error;
typedef struct { size_t max_document_bytes; unsigned max_depth; } yl_limits;
typedef struct yl_value yl_value;
typedef struct yl_document yl_document;
typedef struct { unsigned char *data; size_t size; } yl_buffer;
/* Callback must fill exactly size bytes, or return a nonzero status. */
typedef int (*yl_read_at_fn)(void *context, uint64_t offset, void *buffer, size_t size);
typedef yl_status (*yl_profile_fn)(const yl_document *, void *, yl_error *);
typedef struct { const char *name; const char *version; yl_profile_fn validate; void *context; } yl_profile;
typedef struct { const yl_profile *profiles; size_t count; const char *const *features; size_t feature_count; } yl_registry;
YL_API const char *yl_version(void);
YL_API yl_limits yl_default_limits(void);
YL_API const char *yl_status_name(yl_status status);
YL_API void yl_buffer_free(yl_buffer *buffer);
YL_API yl_value *yl_new(yl_type type);
YL_API yl_value *yl_string(const char *text, size_t size);
YL_API yl_value *yl_integer(int64_t number);
YL_API yl_value *yl_float(double number);
YL_API yl_value *yl_boolean(int boolean);
YL_API yl_value *yl_temporal(const char *kind, const char *text, size_t size);
YL_API void yl_value_free(yl_value *value);
YL_API yl_type yl_value_type(const yl_value *value);
YL_API const char *yl_value_text(const yl_value *value, size_t *size);
YL_API const char *yl_temporal_kind(const yl_value *value);
YL_API int64_t yl_value_integer(const yl_value *value);
YL_API double yl_value_float(const yl_value *value);
YL_API int yl_value_boolean(const yl_value *value);
YL_API size_t yl_count(const yl_value *value);
YL_API const yl_value *yl_at(const yl_value *value, size_t index);
YL_API const char *yl_key(const yl_value *value, size_t index, size_t *size);
YL_API const yl_value *yl_get(const yl_value *table, const char *key, size_t size);
/* Successful insertion transfers ownership; failure leaves ownership unchanged. */
YL_API yl_status yl_set(yl_value *table, const char *key, size_t size, yl_value *value, yl_error *error);
YL_API yl_status yl_append(yl_value *array, yl_value *value, yl_error *error);
/* Successful creation transfers ownership of root. */
YL_API yl_status yl_document_create(yl_value *root, const yl_limits *limits, yl_document **out, yl_error *error);
YL_API yl_status yl_parse(const char *text, size_t size, const yl_limits *limits, yl_document **out, yl_error *error);
YL_API const yl_value *yl_root(const yl_document *document);
YL_API yl_value *yl_root_mutable(yl_document *document);
YL_API void yl_document_free(yl_document *document);
YL_API yl_status yl_validate(const yl_document *document, const yl_registry *registry, yl_error *error);
YL_API yl_status yl_dump(const yl_document *document, yl_buffer *out, yl_error *error);
YL_API yl_status yl_pack(const yl_document *document, yl_buffer *out, yl_error *error);
YL_API yl_status yl_unpack(const void *buffer, size_t size, size_t offset, const yl_limits *limits, yl_document **out, size_t *consumed, yl_error *error);
YL_API yl_status yl_read_at(yl_read_at_fn read, void *context, uint64_t offset, uint64_t available, const yl_limits *limits, yl_document **out, uint64_t *consumed, yl_error *error);
#ifdef __cplusplus
}
#endif
#endif
