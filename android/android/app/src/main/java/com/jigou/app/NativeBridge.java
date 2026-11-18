package com.jigou.app;

import android.webkit.JavascriptInterface;


public class NativeBridge {

    private final MainActivity activity;

    public NativeBridge(MainActivity activity) {
        this.activity = activity;
    }

    @JavascriptInterface
    public void saveTextFile(String filename, String content) {
        activity.runOnUiThread(() -> FileSaver.saveText(activity, filename, content));
    }

    @JavascriptInterface
    public void saveImage(String filename, String dataUrl) {
        activity.runOnUiThread(() -> FileSaver.saveImage(activity, filename, dataUrl));
    }

    @JavascriptInterface
    public String platform() {
        return "android";
    }

    @JavascriptInterface
    public String shellVersion() {
        return "1.1";
    }
}
