package com.jigou.app;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Base64;

import java.nio.charset.StandardCharsets;


public final class Config {

    private static final String PREFS_NAME = "jigou_shell";
    private static final String KEY_H5_URL = "h5_url";

    
    private static final String DEFAULT_H5_URL_ENC = "aHR0cDovLzE0MC4xNDMuMjAzLjEwNi8=";

    private Config() {
    }

    public static String getH5Url(Context context) {
        SharedPreferences sp = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        String url = sp.getString(KEY_H5_URL, null);
        if (url == null || url.trim().isEmpty()) {
            url = decodeDefault();
        }
        return url == null ? "" : url.trim();
    }

    public static void setH5Url(Context context, String url) {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                .edit()
                .putString(KEY_H5_URL, url == null ? "" : url.trim())
                .apply();
    }

    private static String decodeDefault() {
        try {
            byte[] data = Base64.decode(DEFAULT_H5_URL_ENC, Base64.DEFAULT);
            return new String(data, StandardCharsets.UTF_8);
        } catch (Exception e) {
            return "";
        }
    }
}
