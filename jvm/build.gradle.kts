// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
import org.gradle.api.publish.maven.MavenPublication
import org.gradle.plugins.signing.SigningExtension
plugins { base; kotlin("jvm") version "2.4.20" apply false }
version = Regex("\"version\":\\s*\"([^\"]+)\"").find(file("../release/release.json").readText())!!.groupValues[1]
allprojects { group = "io.github.younglionorganization"; version = rootProject.version; repositories { mavenCentral() } }
subprojects {
    apply(plugin = "maven-publish")
    apply(plugin = "signing")
    extensions.configure<PublishingExtension> {
        repositories { maven { name = "staging"; url = rootProject.layout.buildDirectory.dir("maven-repository").get().asFile.toURI() } }
        publications.withType<MavenPublication>().configureEach {
            pom {
                name.set("YLSpec " + project.name)
                description.set("C-backed YLSpec documents for Java, Kotlin, and Android")
                url.set("https://github.com/YoungLionOrganization/YLSpec")
                licenses { license { name.set("Apache License, Version 2.0"); url.set("https://www.apache.org/licenses/LICENSE-2.0") } }
                developers { developer { id.set("Cavanshirpro"); name.set("Cavanşir Qurbanzadə"); email.set("cavanshirpro@gmail.com") } }
                scm { connection.set("scm:git:https://github.com/YoungLionOrganization/YLSpec.git"); developerConnection.set("scm:git:ssh://git@github.com/YoungLionOrganization/YLSpec.git"); url.set("https://github.com/YoungLionOrganization/YLSpec") }
            }
        }
    }
    extensions.configure<SigningExtension> {
        val key = System.getenv("MAVEN_GPG_PRIVATE_KEY")
        isRequired = key != null
        if (key != null) useInMemoryPgpKeys(key, System.getenv("MAVEN_GPG_PASSPHRASE"))
        sign(extensions.getByType<PublishingExtension>().publications)
    }
    tasks.withType<Zip>().configureEach {
        isPreserveFileTimestamps = false
        isReproducibleFileOrder = true
        from(rootProject.file("../LICENSE")) { into("META-INF") }
        from(rootProject.file("../NOTICE")) { into("META-INF") }
        from(rootProject.file("../THIRD_PARTY_NOTICES.md")) { into("META-INF") }
        from(rootProject.file("../vendor/tomlc17/LICENSE")) { into("META-INF/licenses/tomlc17") }
    }
}
