/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
#include "ylspec.h"
#include <stdint.h>
#include <stddef.h>
int LLVMFuzzerTestOneInput(const uint8_t *data,size_t size){yl_document *d=NULL;yl_error e;yl_buffer b={0};yl_limits l={65536,32};if(yl_parse((const char*)data,size,&l,&d,&e)==YL_OK){yl_dump(d,&b,&e);yl_buffer_free(&b);yl_pack(d,&b,&e);yl_buffer_free(&b);yl_document_free(d);}d=NULL;if(yl_unpack(data,size,0,&l,&d,NULL,&e)==YL_OK)yl_document_free(d);return 0;}
