import { Capacitor } from '@capacitor/core';
import { GoogleSignIn } from '@capawesome/capacitor-google-sign-in';

export const isNative = Capacitor.isNativePlatform();

// Web OAuth client ID from Google Cloud Console. On Android the plugin's native
// Credential Manager uses this as the server client ID. Must be configured in
// Google Cloud Console -> APIs & Services -> Credentials -> OAuth 2.0 Client IDs
// (type "Web application").
export const GOOGLE_WEB_CLIENT_ID = import.meta.env.VITE_GOOGLE_WEB_CLIENT_ID ?? '';

// Fully in-app native Google sign-in. Returns an ID token that Supabase can
// verify directly — no redirect, no deep link, no WebView, no Chrome.
export async function nativeGoogleSignIn() {
  await GoogleSignIn.initialize({
    clientId: GOOGLE_WEB_CLIENT_ID,
  });
  const result = await GoogleSignIn.signIn();
  if (!result.idToken) {
    throw new Error('Google returned no ID token');
  }
  return result;
}
