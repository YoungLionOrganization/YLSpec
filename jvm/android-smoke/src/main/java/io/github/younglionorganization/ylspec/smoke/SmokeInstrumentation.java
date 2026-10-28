/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
package io.github.younglionorganization.ylspec.smoke;
import android.app.Activity;
import android.app.Instrumentation;
import android.os.Bundle;
import io.github.younglionorganization.ylspec.*;
import java.util.LinkedHashMap;
import java.util.Map;
/** Runs the packaged JNI library inside an actual Android runtime. */
public final class SmokeInstrumentation extends Instrumentation {
    @Override public void onCreate(Bundle arguments) {super.onCreate(arguments); start();}
    @Override public void onStart() {
        Bundle result = new Bundle();
        try {
            Map<String, Object> values = new LinkedHashMap<>(); values.put("count", Long.MAX_VALUE); values.put("name", "Android JNI");
            Document document = new Document(values);
            if (!YLSpec.unpack(YLSpec.pack(document)).data().equals(values)) throw new AssertionError("Android round-trip failed");
            result.putString("result", "YLSpec Android JNI tests passed"); finish(Activity.RESULT_OK, result);
        } catch (Throwable error) {result.putString("error", error.toString()); finish(Activity.RESULT_CANCELED, result);}
    }
}
