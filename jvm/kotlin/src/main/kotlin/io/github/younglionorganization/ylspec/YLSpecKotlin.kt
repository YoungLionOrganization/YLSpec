// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
@file:JvmName("YLSpecKotlin")
package io.github.younglionorganization.ylspec

/** Construct a C-backed document using idiomatic Kotlin map data. */
fun ylspecDocument(data: Map<String, Any> = emptyMap(), profile: String = "core.data",
                   profileVersion: String = "0.1", limits: Limits = Limits.DEFAULT): Document =
    Document(data, profile, profileVersion, limits)

/** Serialize this mutable envelope through the same JNI C implementation. */
fun Document.toYLSpec(): String = YLSpec.dumps(this)

/** Produce an embeddable frame. Host location and authenticity are separate. */
fun Document.toFrame(): ByteArray = YLSpec.pack(this)

/** Validate the standard core.data profile; custom rules use the Java validator API. */
fun Document.validateYLSpec(): Document = YLSpec.validate(this)

/** Parse standalone metadata without implicitly approving a custom profile. */
fun String.parseYLSpec(limits: Limits = Limits.DEFAULT): Document = YLSpec.loads(this, limits)

/** Decode one frame at an explicit buffer offset. */
fun ByteArray.parseYLSpecFrame(offset: Int = 0, limits: Limits = Limits.DEFAULT): Document =
    YLSpec.unpack(this, offset, limits)
