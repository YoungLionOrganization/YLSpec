/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
package io.github.younglionorganization.ylspec;
import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.CharBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.time.*;
import java.util.*;
/** Private typed transport shared with the C binding adapter, not a file format. */
final class Wire {
    private static final List<String> KINDS = Arrays.asList("date", "time", "datetime", "datetime-offset");
    static byte[] utf8(String text) {
        try {ByteBuffer buffer = StandardCharsets.UTF_8.newEncoder().onMalformedInput(CodingErrorAction.REPORT).encode(CharBuffer.wrap(text)); byte[] bytes = new byte[buffer.remaining()]; buffer.get(bytes); return bytes;}
        catch (CharacterCodingException error) {throw new IllegalArgumentException("Invalid UTF-16 string", error);}
    }
    private final ByteArrayOutputStream out = new ByteArrayOutputStream();
    private final Limits limits;
    private final Set<Object> active = Collections.newSetFromMap(new IdentityHashMap<Object, Boolean>());
    private Wire(Limits limits) {this.limits = limits;}
    private void bytes(byte[] bytes) {if ((long)out.size() + bytes.length > (long)limits.maxDocumentBytes * 8 + 1024) throw new IllegalArgumentException("Binding input limit exceeded"); out.write(bytes, 0, bytes.length);}
    private void number(long value, int size) {byte[] bytes = new byte[size]; for (int i = 0; i < size; i++) bytes[i] = (byte)(value >>> (8 * i)); bytes(bytes);}
    private void text(String value) {byte[] encoded = utf8(value); number(encoded.length, 4); bytes(encoded);}
    private void write(Object value, int depth) {
        if (depth > limits.maxDepth) throw new IllegalArgumentException("Value depth exceeded");
        if (value instanceof LocalDate) value = new TemporalValue("date", value.toString());
        else if (value instanceof LocalTime) value = new TemporalValue("time", value.toString());
        else if (value instanceof LocalDateTime) value = new TemporalValue("datetime", value.toString());
        else if (value instanceof OffsetDateTime || value instanceof Instant) value = new TemporalValue("datetime-offset", value.toString());
        if (value instanceof String) {number(0, 1); text((String)value);}
        else if (value instanceof Byte || value instanceof Short || value instanceof Integer || value instanceof Long) {number(1, 1); number(((Number)value).longValue(), 8);}
        else if (value instanceof Double || value instanceof Float) {number(2, 1); number(Double.doubleToRawLongBits(((Number)value).doubleValue()), 8);}
        else if (value instanceof Boolean) {number(3, 1); number((Boolean)value ? 1 : 0, 1);}
        else if (value instanceof TemporalValue) {TemporalValue temporal = (TemporalValue)value; number(4, 1); number(KINDS.indexOf(temporal.kind), 1); text(temporal.text);}
        else if (value instanceof Map || value instanceof List) {
            if (!active.add(value)) throw new IllegalArgumentException("Cyclic application data");
            if (value instanceof Map) {
                Map<?, ?> map = (Map<?, ?>)value; if (map.size() > 16384) throw new IllegalArgumentException("Container entry limit exceeded");
                number(6, 1); number(map.size(), 4); for (Map.Entry<?, ?> entry : map.entrySet()) {if (!(entry.getKey() instanceof String)) throw new IllegalArgumentException("Table keys must be strings"); text((String)entry.getKey()); write(entry.getValue(), depth + 1);}
            } else {List<?> list = (List<?>)value; if (list.size() > 16384) throw new IllegalArgumentException("Container entry limit exceeded"); number(5, 1); number(list.size(), 4); for (Object item : list) write(item, depth + 1);}
            active.remove(value);
        } else throw new IllegalArgumentException("Unsupported TOML value");
    }
    static byte[] encode(Map<String, Object> root, Limits limits) {Wire writer = new Wire(limits); writer.write(root, 0); return writer.out.toByteArray();}
    private static String text(ByteBuffer buffer) {int count = buffer.getInt(); if (count < 0 || count > buffer.remaining()) throw new IllegalStateException("Invalid native string length"); byte[] bytes = new byte[count]; buffer.get(bytes); return new String(bytes, StandardCharsets.UTF_8);}
    private static Object read(ByteBuffer buffer, int depth) {
        if (depth > 128) throw new IllegalStateException("Invalid native depth");
        switch (buffer.get()) {
            case 0: return text(buffer);
            case 1: return buffer.getLong();
            case 2: return buffer.getDouble();
            case 3: return buffer.get() != 0;
            case 4: return new TemporalValue(KINDS.get(buffer.get()), text(buffer));
            case 5: {int count = buffer.getInt(); List<Object> result = new ArrayList<>(); for (int i = 0; i < count; i++) result.add(read(buffer, depth + 1)); return result;}
            case 6: {int count = buffer.getInt(); Map<String, Object> result = new LinkedHashMap<>(); for (int i = 0; i < count; i++) {String key = text(buffer); result.put(key, read(buffer, depth + 1));} return result;}
            default: throw new IllegalStateException("Unknown native value type");
        }
    }
    @SuppressWarnings("unchecked") static Map<String, Object> decode(byte[] bytes) {ByteBuffer buffer = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN); Map<String, Object> root = (Map<String, Object>)read(buffer, 0); if (buffer.hasRemaining()) throw new IllegalStateException("Trailing native bytes"); return root;}
}
