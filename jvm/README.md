# YLSpec for Java, Kotlin, and Android

Copyright 2026 Cavanşir Qurbanzadə. Apache-2.0.

Both languages call the original C reference implementation through JNI. Java
bytecode targets Java 8; CI uses JDK 17 and 21. Android supports API 26 and newer.
No native handles are retained by Document objects: each operation owns and frees
its temporary C tree before returning.

## Desktop JVM

Coordinates use the namespace `io.github.younglionorganization`:

```kotlin
implementation("io.github.younglionorganization:ylspec:0.1.1")
// Optional idiomatic Kotlin extensions:
implementation("io.github.younglionorganization:ylspec-kotlin:0.1.1")
```

The Java artifact has a runtime dependency on `ylspec-natives`, which bundles
desktop JNI resources. Include that transitive dependency when assembling an
application. The loader selects an OS/architecture resource, extracts it to an
owned temporary directory, and loads it. Applications with controlled loading
can supply an absolute `-Dylspec.native.path=/path/to/library` instead.

```java
import io.github.younglionorganization.ylspec.*;
import java.util.Collections;
Document doc = new Document(Collections.singletonMap("name", "Java"));
byte[] frame = YLSpec.pack(doc);
Document restored = YLSpec.unpack(frame);
```

```kotlin
import io.github.younglionorganization.ylspec.*
val doc = ylspecDocument(mapOf("name" to "Kotlin", "count" to 42L))
val restored = doc.toFrame().parseYLSpecFrame()
```

## Android

Use the common Java/Kotlin API and add the JNI-only Android AAR. Exclude desktop
native resources from the Android dependency graph:

```kotlin
implementation("io.github.younglionorganization:ylspec-kotlin:0.1.1") {
    exclude(group = "io.github.younglionorganization", module = "ylspec-natives")
}
implementation("io.github.younglionorganization:ylspec-android:0.1.1@aar")
```

The AAR supplies armeabi-v7a, arm64-v8a, x86, and x86_64 libraries and consumer
keep rules for JNI class names. It intentionally contains no duplicate Java
classes. The loader calls `System.loadLibrary` on Android. Native compilation
targets API 26. Desktop binary compatibility does not imply Android ABI support;
the Android libraries are separately cross-compiled with the NDK.

## Values and errors

| Value | Contract |
|---|---|
| TOML integer | Long; Byte, Short, and Integer inputs are accepted |
| TOML float | Double; Float inputs are accepted |
| TemporalValue | Exact kind and text, preserving fractional digits |
| java.time values | LocalDate, LocalTime, LocalDateTime, OffsetDateTime, Instant inputs |
| Table / array | String-key Map / List |
| null, cycles, unsupported objects | Rejected |

`YLSpec.validate` checks the core profile; an overload accepts application
validators keyed by `profile@revision` and supported feature names. Unknown
profiles stay inspectable but fail explicit validation without a handler.
`YLSpecException` exposes a symbolic code and payload-relative source position.

`YLSpec.readAt` supports a bounded callback and RandomAccessFile. The latter
restores position and synchronizes on the supplied file. Host formats own
discovery, authenticity, and payload layout. Limits default to 16 MiB/depth 64.

Publication requires namespace verification, a Central Portal user token, and
an OpenPGP signing key. The repository's publishing guide describes the exact
GitHub secret names and account setup. Builds and tests run on GitHub Actions.
