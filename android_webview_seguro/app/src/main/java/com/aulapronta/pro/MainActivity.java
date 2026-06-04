package com.aulapronta.pro;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.net.http.SslError;
import android.os.Bundle;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.SslErrorHandler;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebChromeClient;
import android.webkit.SafeBrowsingResponse;
import android.webkit.WebResourceError;
import android.webkit.WebResourceResponse;
import android.widget.FrameLayout;
import android.widget.ProgressBar;
import android.widget.Toast;

public class MainActivity extends Activity {

    /*
     * TROQUE AQUI PELO LINK FINAL DO RUNSITE DO PROFESSOR.
     * Nunca coloque o link do Admin Center neste APK.
     *
     * Exemplo:
     * private static final String BASE_URL = "https://aulapronta-professor.runsite.app";
     * private static final String ALLOWED_HOST = "aulapronta-professor.runsite.app";
     */
    private static final String BASE_URL = "https://SEU-LINK-DO-PROFESSOR.runsite.app";
    private static final String ALLOWED_HOST = "SEU-LINK-DO-PROFESSOR.runsite.app";

    private WebView webView;
    private ProgressBar progress;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        WebView.setWebContentsDebuggingEnabled(false);

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(7, 16, 24));

        webView = new WebView(this);
        progress = new ProgressBar(this);

        FrameLayout.LayoutParams webParams = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
        );
        root.addView(webView, webParams);

        FrameLayout.LayoutParams progParams = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT
        );
        progParams.gravity = android.view.Gravity.CENTER;
        root.addView(progress, progParams);

        setContentView(root);

        configureWebView();
        webView.loadUrl(BASE_URL);
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void configureWebView() {
        WebSettings s = webView.getSettings();

        // Necessário para o sistema web funcionar, mas sem bridge nativa.
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);

        // Segurança: nada de acesso local.
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setAllowFileAccessFromFileURLs(false);
        s.setAllowUniversalAccessFromFileURLs(false);

        // Segurança: só HTTPS, sem conteúdo misto HTTP dentro do HTTPS.
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);

        // Evita cache local forte para dados sensíveis.
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        webView.clearCache(false);

        // Cookies apenas para o domínio do app; sem terceiros.
        CookieManager cookieManager = CookieManager.getInstance();
        cookieManager.setAcceptCookie(true);
        cookieManager.setAcceptThirdPartyCookies(webView, false);

        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new SecureClient());
        webView.setBackgroundColor(Color.rgb(7, 16, 24));
        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);

        try {
            WebView.startSafeBrowsing(this, success -> {});
        } catch (Exception ignored) {}
    }

    private boolean isAllowedAulaProntaUrl(Uri uri) {
        if (uri == null) return false;

        String scheme = uri.getScheme() == null ? "" : uri.getScheme().toLowerCase();
        String host = uri.getHost() == null ? "" : uri.getHost().toLowerCase();

        return scheme.equals("https") && host.equals(ALLOWED_HOST.toLowerCase());
    }

    private boolean isAllowedExternalUrl(Uri uri) {
        if (uri == null) return false;

        String scheme = uri.getScheme() == null ? "" : uri.getScheme().toLowerCase();
        String host = uri.getHost() == null ? "" : uri.getHost().toLowerCase();

        if (scheme.equals("whatsapp")) return true;

        if (scheme.equals("https")) {
            return host.equals("wa.me")
                    || host.equals("api.whatsapp.com")
                    || host.endsWith(".whatsapp.com");
        }

        return false;
    }

    private void openExternal(Uri uri) {
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW, uri);
            startActivity(intent);
        } catch (ActivityNotFoundException e) {
            Toast.makeText(this, "Não foi possível abrir este link.", Toast.LENGTH_LONG).show();
        }
    }

    private class SecureClient extends WebViewClient {

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            Uri uri = request.getUrl();

            if (isAllowedAulaProntaUrl(uri)) {
                return false;
            }

            if (isAllowedExternalUrl(uri)) {
                openExternal(uri);
                return true;
            }

            Toast.makeText(MainActivity.this, "Link bloqueado por segurança.", Toast.LENGTH_SHORT).show();
            return true;
        }

        @Override
        public void onPageFinished(WebView view, String url) {
            progress.setVisibility(View.GONE);
            super.onPageFinished(view, url);
        }

        @Override
        public void onReceivedSslError(WebView view, SslErrorHandler handler, SslError error) {
            // Nunca continuar com erro SSL.
            handler.cancel();
            Toast.makeText(MainActivity.this, "Conexão insegura bloqueada.", Toast.LENGTH_LONG).show();
        }

        @Override
        public void onSafeBrowsingHit(WebView view, WebResourceRequest request, int threatType, SafeBrowsingResponse callback) {
            callback.backToSafety(true);
            Toast.makeText(MainActivity.this, "Página bloqueada por segurança.", Toast.LENGTH_LONG).show();
        }

        @Override
        public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
            if (request.isForMainFrame()) {
                progress.setVisibility(View.GONE);
                Toast.makeText(MainActivity.this, "Falha ao carregar. Verifique sua internet.", Toast.LENGTH_LONG).show();
            }
            super.onReceivedError(view, request, error);
        }

        @Override
        public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
            Uri uri = request.getUrl();
            if (uri != null && "http".equalsIgnoreCase(uri.getScheme())) {
                return new WebResourceResponse("text/plain", "utf-8", null);
            }
            return super.shouldInterceptRequest(view, request);
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
            return;
        }
        super.onBackPressed();
    }
}
