package com.flatmate.app;

import android.os.Bundle;
import android.webkit.WebView;

import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            // Google blocks OAuth sign-in from embedded WebViews by detecting the
            // "; wv" marker in the default Android WebView user agent. Strip it so
            // the in-app Google login is treated like a normal browser.
            WebView wv = bridge.getWebView();
            String ua = wv.getSettings().getUserAgentString();
            wv.getSettings().setUserAgentString(ua.replace("; wv", ""));
        } catch (Exception ignored) {
        }
    }
}
