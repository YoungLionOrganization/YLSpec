/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
package io.github.younglionorganization.ylspec;
import java.util.LinkedHashMap;
import java.util.Map;
/** Mutable standard envelope. Native memory is scoped to each operation, not retained here. */
public final class Document {
    public final Map<String, Object> root;
    public final Limits limits;
    public Document() {this(new LinkedHashMap<String, Object>());}
    public Document(Map<String, ?> data) {this(data, "core.data", "0.1", Limits.DEFAULT);}
    public Document(Map<String, ?> data, String profile, String revision, Limits limits) {
        this.limits = limits; root = new LinkedHashMap<>(); Map<String, Object> metadata = new LinkedHashMap<>();
        metadata.put("version", "0.1"); metadata.put("profile", profile); metadata.put("profile_version", revision);
        root.put("_ylspec", metadata); root.put("data", new LinkedHashMap<String, Object>(data));
    }
    Document(Map<String, Object> root, Limits limits) {this.root = root; this.limits = limits;}
    @SuppressWarnings("unchecked") public Map<String, Object> data() {return (Map<String, Object>)root.get("data");}
    @SuppressWarnings("unchecked") public Map<String, Object> metadata() {return (Map<String, Object>)root.get("_ylspec");}
    @SuppressWarnings("unchecked") public Map<String, Object> extensions() {if (!root.containsKey("extensions")) root.put("extensions", new LinkedHashMap<String, Object>()); return (Map<String, Object>)root.get("extensions");}
}
