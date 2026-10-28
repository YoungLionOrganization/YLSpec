// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
plugins { base; `maven-publish` }
val aar by tasks.registering(Zip::class) { archiveBaseName.set("ylspec-android"); archiveExtension.set("aar"); from("src/main") }
val sources by tasks.registering(Jar::class) { archiveClassifier.set("sources"); from(rootProject.file("../bindings")) { include("**/*.c", "**/*.h") }; from("src/main/AndroidManifest.xml") }
val docs by tasks.registering(Jar::class) { archiveClassifier.set("javadoc"); from(rootProject.file("docs")) }
publishing { publications { create<MavenPublication>("library") { artifactId = "ylspec-android"; artifact(aar); artifact(sources); artifact(docs); pom.packaging = "aar" } } }
