/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
package io.github.younglionorganization.ylspec;
/** Structured native failure. Positions are payload-relative; zero line/column means unavailable. */
public final class YLSpecException extends IllegalArgumentException {
    private static final long serialVersionUID = 1L;
    public final String code;
    public final long offset, line, column;
    public YLSpecException(String message, String code, long offset, long line, long column) {
        super(message); this.code = code; this.offset = offset; this.line = line; this.column = column;
    }
}
