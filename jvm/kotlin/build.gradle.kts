// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
plugins { kotlin("jvm"); `java-library`; `maven-publish` }
java { withSourcesJar() }
kotlin { compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_1_8) } }
tasks.withType<JavaCompile>().configureEach { options.release.set(8) }
dependencies { api(project(":java")) }
val docs by tasks.registering(Jar::class) { archiveClassifier.set("javadoc"); from(project.file("docs")) }
tasks.register<JavaExec>("smokeTest") { dependsOn(tasks.testClasses); classpath = sourceSets.test.get().runtimeClasspath; mainClass.set("io.github.younglionorganization.ylspec.KotlinSmokeKt"); systemProperty("ylspec.native.path", System.getProperty("ylspec.native.path", "")) }
publishing { publications { create<MavenPublication>("library") { artifactId = "ylspec-kotlin"; from(components["java"]); artifact(docs) } } }
