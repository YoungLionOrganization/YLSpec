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
        System.out.println("Java JNI smoke tests passed");
    }
}
