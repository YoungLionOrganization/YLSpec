/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
package io.github.younglionorganization.ylspec;
import java.util.*;
public final class SmokeTest {
    public static void main(String[] args) throws Exception {
        Map<String, Object> data = new LinkedHashMap<>(); data.put("integer", Long.MAX_VALUE); data.put("name", "Hello 🌍"); data.put("time", new TemporalValue("datetime-offset", "2026-10-28T12:34:56.123456789Z"));
        Document document = YLSpec.validate(new Document(data)); byte[] frame = YLSpec.pack(document); Document restored = YLSpec.unpack(frame);
        if (!data.equals(restored.data())) throw new AssertionError("Round-trip mismatch");
        final int[] reads = {0}; Document streamed = YLSpec.readAt((position, size) -> {reads[0]++; return Arrays.copyOfRange(frame, (int)position, (int)position + size);}, 0, frame.length, Limits.DEFAULT);
        if (reads[0] != 2 || !streamed.data().equals(data)) throw new AssertionError("Unbounded read");
        for (int i = 0; i < frame.length; i++) {try {YLSpec.unpack(Arrays.copyOf(frame, i)); throw new AssertionError("Accepted truncated frame");} catch (YLSpecException expected) {}}
        try {YLSpec.loads("invalid"); throw new AssertionError("Accepted invalid document");} catch (YLSpecException expected) {if (expected.code == null) throw new AssertionError();}
        byte[] host = new byte[9 + frame.length * 2]; System.arraycopy(frame, 0, host, 7, frame.length); System.arraycopy(frame, 0, host, 7 + frame.length, frame.length);
        if (!YLSpec.unpack(host, 7, Limits.DEFAULT).data().equals(data) || !YLSpec.unpack(host, 7 + frame.length, Limits.DEFAULT).data().equals(data)) throw new AssertionError("Multiple unaligned frame mismatch");
        byte[] oversized = Arrays.copyOf(frame, 32);
        java.nio.ByteBuffer.wrap(oversized).order(java.nio.ByteOrder.LITTLE_ENDIAN).putLong(16, Integer.MAX_VALUE);
        final int[] rejectedReads = {0};
        try {YLSpec.readAt((position, size) -> {rejectedReads[0]++; if (size != 32) throw new AssertionError("Requested oversized payload"); return oversized;}, 0, 32L + Integer.MAX_VALUE, new Limits(Integer.MAX_VALUE, 64)); throw new AssertionError("Accepted oversized Java frame");} catch (IllegalArgumentException expected) {}
        if (rejectedReads[0] != 1) throw new AssertionError("Expected header-only rejection");
        System.out.println("Java JNI smoke tests passed");
    }
}
