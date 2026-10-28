// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
plugins { id("com.android.application") version "8.13.0" }
val releaseVersion = Regex("\"version\":\\s*\"([^\"]+)\"").find(file("../../release/release.json").readText())!!.groupValues[1]
android {
    namespace = "io.github.younglionorganization.ylspec.smoke"
    compileSdk = 35
    defaultConfig { applicationId = namespace; minSdk = 26; targetSdk = 35; versionCode = 1; versionName = releaseVersion }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_1_8; targetCompatibility = JavaVersion.VERSION_1_8 }
}
dependencies {
    implementation(files("../java/build/libs/java-$releaseVersion.jar"))
    implementation(files("../android/build/distributions/ylspec-android-$releaseVersion.aar"))
}
