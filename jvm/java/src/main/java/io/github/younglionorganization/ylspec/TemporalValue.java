/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
package io.github.younglionorganization.ylspec;
import java.util.Arrays;
import java.util.Objects;
/** Exact TOML temporal token. Validation of its text is performed by the C serializer. */
public final class TemporalValue {
    public final String kind;
    public final String text;
    public TemporalValue(String kind, String text) {
        if (!Arrays.asList("date", "time", "datetime", "datetime-offset").contains(kind)) throw new IllegalArgumentException("Invalid temporal kind");
        this.kind = kind; this.text = Objects.requireNonNull(text);
    }
    @Override public boolean equals(Object other) {return other instanceof TemporalValue && kind.equals(((TemporalValue)other).kind) && text.equals(((TemporalValue)other).text);}
    @Override public int hashCode() {return Objects.hash(kind, text);}
    @Override public String toString() {return text;}
}
