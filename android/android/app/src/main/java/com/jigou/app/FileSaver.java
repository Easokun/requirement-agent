package com.jigou.app;

import android.app.Activity;
import android.content.ContentValues;
import android.content.Context;
import android.media.MediaScannerConnection;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;


public final class FileSaver {

    private FileSaver() {
    }

    public static void saveText(Activity activity, String filename, String content) {
        PermissionHelper.ensureStoragePermission(activity, granted -> {
            if (!granted) {
                Toast.makeText(activity, "未授予存储权限，无法保存文件", Toast.LENGTH_LONG).show();
                return;
            }
            doSave(activity, filename, content);
        });
    }

    private static void doSave(Activity activity, String filename, String content) {
        String safeName = sanitize(filename);
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                saveViaMediaStore(activity, safeName, content);
            } else {
                saveViaFile(activity, safeName, content);
            }

            File shareCopy = new File(activity.getCacheDir(), safeName);
            try (OutputStream os = new FileOutputStream(shareCopy)) {
                os.write(content.getBytes(StandardCharsets.UTF_8));
            }

            showSavedDialog(activity, safeName, shareCopy);
        } catch (Exception e) {
            Toast.makeText(activity, "保存失败：" + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private static void saveViaMediaStore(Context context, String name, String content)
            throws Exception {
        ContentValues values = new ContentValues();
        values.put(MediaStore.Downloads.DISPLAY_NAME, name);
        values.put(MediaStore.Downloads.MIME_TYPE, "text/markdown");
        values.put(MediaStore.Downloads.IS_PENDING, 1);

        Uri uri = context.getContentResolver()
                .insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
        if (uri == null) {
            throw new IllegalStateException("无法创建下载文件");
        }
        try (OutputStream os = context.getContentResolver().openOutputStream(uri)) {
            if (os == null) {
                throw new IllegalStateException("无法写入下载文件");
            }
            os.write(content.getBytes(StandardCharsets.UTF_8));
        } catch (Exception e) {
            context.getContentResolver().delete(uri, null, null);
            throw e;
        }

        values.clear();
        values.put(MediaStore.Downloads.IS_PENDING, 0);
        context.getContentResolver().update(uri, values, null, null);
    }

    private static void saveViaFile(Context context, String name, String content)
            throws Exception {
        File dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
        if (!dir.exists() && !dir.mkdirs()) {
            throw new IllegalStateException("无法创建下载目录");
        }
        File file = new File(dir, name);
        try (OutputStream os = new FileOutputStream(file)) {
            os.write(content.getBytes(StandardCharsets.UTF_8));
        }
        MediaScannerConnection.scanFile(
                context,
                new String[]{file.getAbsolutePath()},
                new String[]{"text/markdown"},
                null);
    }

    private static void showSavedDialog(Activity activity, String name, File shareCopy) {
        new AlertDialog.Builder(activity)
                .setTitle(R.string.saved_title)
                .setMessage("文件已保存到「下载」目录：\n" + name)
                .setPositiveButton(R.string.share,
                        (dialog, which) -> ShareHelper.shareFile(activity, shareCopy))
                .setNegativeButton(R.string.done, null)
                .show();
    }

    
    public static void saveImage(Activity activity, String filename, String dataUrl) {
        PermissionHelper.ensureStoragePermission(activity, granted -> {
            if (!granted) {
                Toast.makeText(activity, "未授予存储权限，无法保存图片", Toast.LENGTH_LONG).show();
                return;
            }
            doSaveImage(activity, filename, dataUrl);
        });
    }

    private static void doSaveImage(Activity activity, String filename, String dataUrl) {
        String safeName = sanitize(filename);
        if (!safeName.toLowerCase().endsWith(".png")) {
            safeName += ".png";
        }
        try {
            String base64 = dataUrl == null ? "" : dataUrl;
            int comma = base64.indexOf(',');
            if (base64.startsWith("data:") && comma > 0) {
                base64 = base64.substring(comma + 1);
            }
            byte[] bytes = Base64.decode(base64, Base64.DEFAULT);
            if (bytes.length == 0) {
                throw new IllegalStateException("图片内容为空");
            }

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                saveImageViaMediaStore(activity, safeName, bytes);
            } else {
                saveImageViaFile(activity, safeName, bytes);
            }
            Toast.makeText(activity, "已保存到相册", Toast.LENGTH_SHORT).show();
        } catch (Exception e) {
            Toast.makeText(activity, "保存失败：" + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private static void saveImageViaMediaStore(Context context, String name, byte[] bytes)
            throws Exception {
        ContentValues values = new ContentValues();
        values.put(MediaStore.Images.Media.DISPLAY_NAME, name);
        values.put(MediaStore.Images.Media.MIME_TYPE, "image/png");
        values.put(MediaStore.Images.Media.RELATIVE_PATH,
                Environment.DIRECTORY_PICTURES + "/极构");
        values.put(MediaStore.Images.Media.IS_PENDING, 1);

        Uri uri = context.getContentResolver()
                .insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
        if (uri == null) {
            throw new IllegalStateException("无法创建图片");
        }
        try (OutputStream os = context.getContentResolver().openOutputStream(uri)) {
            if (os == null) {
                throw new IllegalStateException("无法写入图片");
            }
            os.write(bytes);
        } catch (Exception e) {
            context.getContentResolver().delete(uri, null, null);
            throw e;
        }

        values.clear();
        values.put(MediaStore.Images.Media.IS_PENDING, 0);
        context.getContentResolver().update(uri, values, null, null);
    }

    private static void saveImageViaFile(Context context, String name, byte[] bytes)
            throws Exception {
        File dir = new File(
                Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES),
                "极构");
        if (!dir.exists() && !dir.mkdirs()) {
            throw new IllegalStateException("无法创建相册目录");
        }
        File file = new File(dir, name);
        try (OutputStream os = new FileOutputStream(file)) {
            os.write(bytes);
        }
        MediaScannerConnection.scanFile(
                context,
                new String[]{file.getAbsolutePath()},
                new String[]{"image/png"},
                null);
    }

    private static String sanitize(String filename) {
        String name = (filename == null || filename.trim().isEmpty())
                ? "需求诊断报告.md"
                : filename.trim();
        return name.replaceAll("[\\\\/:*?\"<>|]", "_");
    }
}
