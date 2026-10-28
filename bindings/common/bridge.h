/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
#ifndef YLSPEC_BINDING_BRIDGE_H
#define YLSPEC_BINDING_BRIDGE_H
#include "ylspec.h"
/* Internal binding transport, not a YLSpec file format or public wire standard.
 * Operations: 0=text to typed tree, 1=tree to text, 2=tree to frame, 3=frame to tree.
 * Values: one yl_type byte, then LE lengths/counts and scalar data. */
yl_status yl_bridge_process(int operation, const unsigned char *input, size_t size, size_t offset,
                            const yl_limits *limits, yl_buffer *output, yl_error *error);
#endif
