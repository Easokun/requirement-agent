package com.jigou.app;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.os.Build;

import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;


public final class PermissionHelper {

    public static final int REQUEST_STORAGE = 1001;

    public interface Callback {
        void onResult(boolean granted);
    }

    private static Callback pendingCallback;

    private PermissionHelper() {
    }

    public static void ensureStoragePermission(Activity activity, Callback callback) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q
                || hasStoragePermission(activity)) {
            callback.onResult(true);
            return;
        }
        pendingCallback = callback;
        ActivityCompat.requestPermissions(
                activity,
                new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE},
                REQUEST_STORAGE);
    }

    public static void onRequestPermissionsResult(int requestCode, int[] grantResults) {
        if (requestCode != REQUEST_STORAGE || pendingCallback == null) {
            return;
        }
        Callback callback = pendingCallback;
        pendingCallback = null;
        boolean granted = grantResults.length > 0
                && grantResults[0] == PackageManager.PERMISSION_GRANTED;
        callback.onResult(granted);
    }

    private static boolean hasStoragePermission(Activity activity) {
        return ContextCompat.checkSelfPermission(
                activity, Manifest.permission.WRITE_EXTERNAL_STORAGE)
                == PackageManager.PERMISSION_GRANTED;
    }
}
