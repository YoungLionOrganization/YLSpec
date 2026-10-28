// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
plugins { `java-library`; `maven-publish` }
java { withSourcesJar(); withJavadocJar() }
tasks.withType<JavaCompile>().configureEach { options.release.set(8); options.encoding = "UTF-8" }
tasks.withType<Javadoc>().configureEach { (options as StandardJavadocDocletOptions).addStringOption("Xdoclint:none", "-quiet") }
dependencies { runtimeOnly(project(":natives")) }
tasks.register<JavaExec>("smokeTest") { dependsOn(tasks.testClasses); classpath = sourceSets.test.get().runtimeClasspath; mainClass.set("io.github.younglionorganization.ylspec.SmokeTest"); systemProperty("ylspec.native.path", System.getProperty("ylspec.native.path", "")) }
publishing { publications { create<MavenPublication>("library") { artifactId = "ylspec"; from(components["java"]) } } }
