package com.jigou.app;

import android.app.Activity;
import android.content.Context;
import android.net.Uri;
import android.os.Environment;
import android.webkit.CookieManager;
import android.webkit.URLUtil;
import android.widget.Toast;

import android.app.DownloadManager;


public final class DownloadHelper {

    private DownloadHelper() {
    }

    public static void enqueue(Activity activity, String url, String userAgent,
                               String contentDisposition, String mimeType) {
        try {
            DownloadManager.Request request = new DownloadManager.Request(Uri.parse(url));
            if (mimeType != null) {
                request.setMimeType(mimeType);
            }
            String cookie = CookieManager.getInstance().getCookie(url);
            if (cookie != null) {
                request.addRequestHeader("Cookie", cookie);
            }
            if (userAgent != null) {
                request.addRequestHeader("User-Agent", userAgent);
            }

            String name = URLUtil.guessFileName(url, contentDisposition, mimeType);
            request.setTitle(name);
            request.setDescription("正在下载");
            request.setNotificationVisibility(
                    DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, name);

            DownloadManager manager =
                    (DownloadManager) activity.getSystemService(Context.DOWNLOAD_SERVICE);
            if (manager == null) {
                Toast.makeText(activity, "系统下载服务不可用", Toast.LENGTH_LONG).show();
                return;
            }
            manager.enqueue(request);
            Toast.makeText(activity, "已开始下载：" + name, Toast.LENGTH_SHORT).show();
        } catch (Exception e) {
            Toast.makeText(activity, "下载失败：" + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }
}
