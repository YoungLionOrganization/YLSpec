/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
package io.github.younglionorganization.ylspec;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.*;
/** C-backed document operations shared by desktop JVMs and Android API 26+. */
public final class YLSpec {
    private YLSpec() {}
    public interface ProfileValidator {boolean validate(Document document);}
    public interface Reader {byte[] read(long offset, int size) throws IOException;}
    public static Document loads(String text) {return loads(text, Limits.DEFAULT);}
    public static Document loads(String text, Limits limits) {return new Document(Wire.decode(Native.process(0, Wire.utf8(text), 0, limits.maxDocumentBytes, limits.maxDepth)), limits);}
    public static String dumps(Document document) {return new String(Native.process(1, Wire.encode(document.root, document.limits), 0, document.limits.maxDocumentBytes, document.limits.maxDepth), StandardCharsets.UTF_8);}
    public static byte[] pack(Document document) {return Native.process(2, Wire.encode(document.root, document.limits), 0, document.limits.maxDocumentBytes, document.limits.maxDepth);}
    public static Document unpack(byte[] bytes) {return unpack(bytes, 0, Limits.DEFAULT);}
    public static Document unpack(byte[] bytes, int offset, Limits limits) {return new Document(Wire.decode(Native.process(3, bytes, offset, limits.maxDocumentBytes, limits.maxDepth)), limits);}
    public static Document validate(Document document) {return validate(document, Collections.<String, ProfileValidator>emptyMap(), Collections.<String>emptySet());}
    public static Document validate(Document document, Map<String, ProfileValidator> validators, Set<String> features) {
        dumps(document); Object required = document.metadata().get("requires");
        if (required instanceof List) for (Object feature : (List<?>)required) if (!features.contains(feature)) throw new YLSpecException("Unsupported required feature: " + feature, "unsupported", 0, 0, 0);
        String key = document.metadata().get("profile") + "@" + document.metadata().get("profile_version");
        if (key.equals("core.data@0.1")) return document;
        ProfileValidator validator = validators.get(key); if (validator == null) throw new YLSpecException("Unsupported profile: " + key, "unsupported", 0, 0, 0);
        if (!validator.validate(document)) throw new YLSpecException("Profile rejected document", "profile", 0, 0, 0); return document;
    }
    /** Read only a supplied frame region; no host format is scanned or executed. */
    public static Document readAt(Reader reader, long offset, long available, Limits limits) throws IOException {
        if (offset < 0 || available < 32 || offset > Long.MAX_VALUE - available) throw new IllegalArgumentException("Invalid frame region");
        byte[] header = reader.read(offset, 32); if (header == null || header.length != 32) throw new IOException("Short frame header read");
        if (!Arrays.equals(Arrays.copyOf(header, 8), new byte[]{89,76,83,80,69,67,0,0})) throw new YLSpecException("Invalid frame magic", "frame", 0, 0, 0);
        ByteBuffer info = ByteBuffer.wrap(header).order(ByteOrder.LITTLE_ENDIAN);
        if (info.getShort(8) != 0 || info.getShort(10) != 1 || info.getInt(12) != 32 || info.getInt(24) != 1 || info.getInt(28) != 0) throw new YLSpecException("Unsupported frame header", "unsupported", 0, 0, 0);
        long size = info.getLong(16); if (size < 0 || size > limits.maxDocumentBytes) throw new YLSpecException("Document byte limit exceeded", "limit", 0, 0, 0);
        if (size > available - 32) throw new YLSpecException("Truncated frame region", "frame", 0, 0, 0);
        if (size > Integer.MAX_VALUE - 32) throw new IllegalArgumentException("Frame exceeds Java array limit");
        byte[] payload = reader.read(offset + 32, (int)size); if (payload == null || payload.length != size) throw new IOException("Short frame payload read");
        byte[] frame = new byte[32 + (int)size]; System.arraycopy(header, 0, frame, 0, 32); System.arraycopy(payload, 0, frame, 32, payload.length); return unpack(frame, 0, limits);
    }
    /** Preserve position and serialize access to a RandomAccessFile during reading. */
    public static Document readAt(final RandomAccessFile file, long offset, long available, Limits limits) throws IOException {
        synchronized (file) {long original = file.getFilePointer(); try {return readAt(new Reader(){public byte[] read(long position, int size) throws IOException {file.seek(position); byte[] bytes = new byte[size]; file.readFully(bytes); return bytes;}}, offset, available, limits);} finally {file.seek(original);}}
    }
}
