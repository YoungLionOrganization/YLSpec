/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
package io.github.younglionorganization.ylspec;
/** Immutable text-byte and value-depth limits. A frame's header is additional. */
public final class Limits {
    public static final Limits DEFAULT = new Limits(16777216, 64);
    public final int maxDocumentBytes;
    public final int maxDepth;
    public Limits(int bytes, int depth) {
        if (bytes < 1 || depth < 1 || depth > 128) throw new IllegalArgumentException("Invalid resource limits");
        maxDocumentBytes = bytes; maxDepth = depth;
    }
}
