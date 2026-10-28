/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
package io.github.younglionorganization.ylspec;
import java.io.File;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.Locale;
/** Internal native loader. Android loads the AAR library; desktop loads a resource or explicit path. */
final class Native {
    static {
        String explicit = System.getProperty("ylspec.native.path", "");
        if (!explicit.isEmpty()) System.load(new File(explicit).getAbsolutePath());
        else if (System.getProperty("java.runtime.name", "").toLowerCase(Locale.ROOT).contains("android") || System.getProperty("java.vm.name", "").equals("Dalvik")) System.loadLibrary("ylspec_jni");
        else {
            String os = System.getProperty("os.name").toLowerCase(Locale.ROOT);
            os = os.contains("win") ? "windows" : os.contains("mac") ? "macos" : os.contains("linux") ? "linux" : os;
            String arch = System.getProperty("os.arch").toLowerCase(Locale.ROOT);
            arch = arch.equals("amd64") || arch.equals("x86_64") ? "x86_64" : arch.equals("aarch64") ? "arm64" : arch;
            String target = os + "-" + arch;
            if (os.equals("linux") && (new File("/lib/ld-musl-x86_64.so.1").exists() || new File("/lib/ld-musl-aarch64.so.1").exists())) target += "-musl";
            String resource = "/natives/" + target + "/" + System.mapLibraryName("ylspec_jni");
            try (InputStream input = Native.class.getResourceAsStream(resource)) {
                if (input == null) throw new UnsatisfiedLinkError("No YLSpec native library for " + target + "; include ylspec-natives or set ylspec.native.path");
                Path directory = Files.createTempDirectory("ylspec-"); Path library = directory.resolve(System.mapLibraryName("ylspec_jni"));
                Files.copy(input, library, StandardCopyOption.REPLACE_EXISTING); directory.toFile().deleteOnExit(); library.toFile().deleteOnExit(); System.load(library.toAbsolutePath().toString());
            } catch (java.io.IOException exception) {throw new ExceptionInInitializerError(exception);}
        }
    }
    static native byte[] process(int operation, byte[] input, long offset, long maximum, int depth);
    private Native() {}
}
