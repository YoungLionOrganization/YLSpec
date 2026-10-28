// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
package io.github.younglionorganization.ylspec
fun main() {
    val original = ylspecDocument(mapOf("name" to "Kotlin", "integer" to Long.MAX_VALUE))
    check(original.validateYLSpec().toFrame().parseYLSpecFrame().data() == original.data())
    check(original.toYLSpec().parseYLSpec().data() == original.data())
    println("Kotlin JNI smoke tests passed")
}
