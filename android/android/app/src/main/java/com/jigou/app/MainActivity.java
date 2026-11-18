package com.jigou.app;

import android.annotation.SuppressLint;
import android.content.Context;
import android.content.Intent;
import android.net.ConnectivityManager;
import android.net.Uri;
import android.os.Bundle;
import android.text.InputType;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ProgressBar;
import android.widget.Toast;

import androidx.activity.OnBackPressedCallback;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;
import androidx.core.view.WindowInsetsControllerCompat;


public class MainActivity extends AppCompatActivity {

    private WebView webView;
    private ProgressBar progressBar;
    private View errorView;
    private View splash;
    private long lastBackPressAt = 0;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        getWindow().setStatusBarColor(ContextCompat.getColor(this, R.color.brand));
        getWindow().setNavigationBarColor(ContextCompat.getColor(this, R.color.surface));
        new WindowInsetsControllerCompat(getWindow(), getWindow().getDecorView())
                .setAppearanceLightStatusBars(false);

        progressBar = findViewById(R.id.progress);
        errorView = findViewById(R.id.errorView);
        splash = findViewById(R.id.splash);

        setupWebView();
        setupActions();
        setupBackPress();

        Intent intent = getIntent();
        if (intent != null && intent.getStringExtra("url") != null) {
            Config.setH5Url(this, intent.getStringExtra("url"));
        }

        loadHome();
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void setupWebView() {
        webView = findViewById(R.id.webview);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);
        
        settings.setCacheMode(WebSettings.LOAD_NO_CACHE);

        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true);

        webView.addJavascriptInterface(new NativeBridge(this), "JiGouNative");
        webView.setWebViewClient(new ShellWebViewClient());
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int newProgress) {
                progressBar.setProgress(newProgress);
                progressBar.setVisibility(newProgress >= 100 ? View.GONE : View.VISIBLE);
            }
        });
        webView.setDownloadListener((url, userAgent, contentDisposition, mimeType, contentLength) ->
                DownloadHelper.enqueue(this, url, userAgent, contentDisposition, mimeType));
    }

    private void setupActions() {
        findViewById(R.id.retryBtn).setOnClickListener(v -> loadHome());
        
        findViewById(R.id.errorIcon).setOnLongClickListener(v -> {
            showUrlDialog();
            return true;
        });
        findViewById(R.id.splashLogo).setOnLongClickListener(v -> {
            showUrlDialog();
            return true;
        });
    }

    private void setupBackPress() {
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                if (webView != null && webView.canGoBack()) {
                    webView.goBack();
                    return;
                }
                long now = System.currentTimeMillis();
                if (now - lastBackPressAt < 2000) {
                    finish();
                } else {
                    lastBackPressAt = now;
                    Toast.makeText(MainActivity.this, R.string.press_again_exit,
                            Toast.LENGTH_SHORT).show();
                }
            }
        });
    }

    private void loadHome() {
        errorView.setVisibility(View.GONE);
        splash.setAlpha(1f);
        splash.setVisibility(View.VISIBLE);
        if (!hasActiveNetwork()) {
            showError();
            return;
        }
        webView.loadUrl(Config.getH5Url(this));
    }

    private boolean hasActiveNetwork() {
        ConnectivityManager cm =
                (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
        return cm != null && cm.getActiveNetwork() != null;
    }

    private void hideSplash() {
        if (splash.getVisibility() != View.VISIBLE) {
            return;
        }
        splash.animate()
                .alpha(0f)
                .setDuration(260)
                .withEndAction(() -> splash.setVisibility(View.GONE))
                .start();
    }

    private void showError() {
        hideSplash();
        errorView.setAlpha(0f);
        errorView.setVisibility(View.VISIBLE);
        errorView.animate().alpha(1f).setDuration(200).start();
    }

    private void showUrlDialog() {
        EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_TEXT_VARIATION_URI);
        input.setText("");

        int pad = (int) (getResources().getDisplayMetrics().density * 20);
        FrameLayout container = new FrameLayout(this);
        container.setPadding(pad, pad / 2, pad, 0);
        container.addView(input, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.WRAP_CONTENT));

        new AlertDialog.Builder(this)
                .setTitle(R.string.url_dialog_title)
                .setMessage(R.string.url_dialog_hint)
                .setView(container)
                .setPositiveButton(R.string.save, (dialog, which) -> {
                    String url = input.getText().toString().trim();
                    if (!url.startsWith("http://") && !url.startsWith("https://")) {
                        url = "http://" + url;
                    }
                    Config.setH5Url(this, url);
                    loadHome();
                })
                .setNegativeButton(R.string.cancel, null)
                .show();
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions,
                                           @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        PermissionHelper.onRequestPermissionsResult(requestCode, grantResults);
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (webView != null) {
            webView.onPause();
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (webView != null) {
            webView.onResume();
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }

    private class ShellWebViewClient extends WebViewClient {

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            Uri uri = request.getUrl();
            String scheme = uri.getScheme() == null ? "" : uri.getScheme();
            if (scheme.equals("http") || scheme.equals("https")) {
                return false;
            }
            try {
                startActivity(new Intent(Intent.ACTION_VIEW, uri));
            } catch (Exception ignored) {
            }
            return true;
        }

        @Override
        public void onPageFinished(WebView view, String url) {
            hideSplash();
        }

        @Override
        public void onReceivedError(WebView view, WebResourceRequest request,
                                    WebResourceError error) {
            if (request.isForMainFrame()) {
                showError();
            }
        }
    }
}
