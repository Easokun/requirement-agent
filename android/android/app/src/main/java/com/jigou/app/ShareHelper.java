package com.jigou.app;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.widget.Toast;

import androidx.core.content.FileProvider;

import java.io.File;


public final class ShareHelper {

    private ShareHelper() {
    }

    public static void shareFile(Activity activity, File file) {
        try {
            Uri uri = FileProvider.getUriForFile(
                    activity,
                    activity.getPackageName() + ".fileprovider",
                    file);

            Intent intent = new Intent(Intent.ACTION_SEND);
            intent.setType("text/markdown");
            intent.putExtra(Intent.EXTRA_STREAM, uri);
            intent.putExtra(Intent.EXTRA_SUBJECT, file.getName());
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);

            activity.startActivity(Intent.createChooser(
                    intent, activity.getString(R.string.share_chooser)));
        } catch (Exception e) {
            Toast.makeText(activity, "分享失败：" + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }
}
