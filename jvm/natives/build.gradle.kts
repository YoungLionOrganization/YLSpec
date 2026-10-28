// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
plugins { `java-library`; `maven-publish` }
java { withSourcesJar() }
tasks.named<Jar>("sourcesJar") { from(rootProject.file("../bindings")) { include("**/*.c", "**/*.h") }; from(rootProject.file("../include")) }
val docs by tasks.registering(Jar::class) { archiveClassifier.set("javadoc"); from(rootProject.file("docs")) }
publishing { publications { create<MavenPublication>("library") { artifactId = "ylspec-natives"; from(components["java"]); artifact(docs) } } }
