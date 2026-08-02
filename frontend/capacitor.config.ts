import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.flatmate.app',
  appName: 'Flatmate',
  webDir: 'dist',
  server: {
    // Keep Google's OAuth flow inside the app's WebView instead of handing it
    // off to the system browser. These hosts are part of the sign-in chain:
    // accounts.google.com (login) -> supabase.co callback -> back to localhost.
    allowNavigation: [
      'accounts.google.com',
      '*.google.com',
      '*.googleusercontent.com',
      '*.gstatic.com',
      'puotstuiwnjutpfjefqv.supabase.co',
    ],
  },
  android: {
    allowMixedContent: false,
  },
};

export default config;
