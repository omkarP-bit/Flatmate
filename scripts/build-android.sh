#!/usr/bin/env bash
#
# Flatmate — Android APK / AAB build script.
#
# Usage:
#   ./scripts/build-android.sh apk     # build signed APK (sideload)
#   ./scripts/build-android.sh aab     # build signed AAB (Play Store)
#   ./scripts/build-android.sh both    # build both (default)
#
# Requires:
#   - node/npm (already present for the web build)
#   - JDK 21  (JAVA_HOME)
#   - Android SDK  (ANDROID_HOME, platform 36 + build-tools 36.0.0)
#
# Signing keystore: android/flatmate-release.keystore (alias: flatmate)
# Override secrets via env: FLATMATE_KEYSTORE, FLATMATE_STORE_PASS,
#                           FLATMATE_KEY_ALIAS, FLATMATE_KEY_PASS
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONT="$ROOT/frontend"
ANDROID="$FRONT/android"

if [ -z "${JAVA_HOME:-}" ]; then
  echo "ERROR: JAVA_HOME not set (need JDK 17 or 21)."
  exit 1
fi
if [ -z "${ANDROID_HOME:-}" ]; then
  echo "ERROR: ANDROID_HOME not set (need Android SDK with platform-36 + build-tools 36.0.0)."
  exit 1
fi

GRADLE="$(command -v gradle || true)"
if [ -z "$GRADLE" ]; then
  if [ -x "$ANDROID_HOME/gradle-8.14.3/bin/gradle" ]; then
    GRADLE="$ANDROID_HOME/gradle-8.14.3/bin/gradle"
  elif [ -x /tmp/opencode/android-build/gradle-8.14.3/bin/gradle ]; then
    GRADLE=/tmp/opencode/android-build/gradle-8.14.3/bin/gradle
  else
    echo "ERROR: gradle not found. Install Gradle 8.14.3 or set PATH."
    exit 1
  fi
fi

MODE="${1:-both}"

echo "==> Building web assets"
cd "$FRONT"
npm run build
npx cap sync android

echo "==> Building Android (mode: $MODE)"
cd "$ANDROID"
if [ "$MODE" = "apk" ] || [ "$MODE" = "both" ]; then
  "$GRADLE" assembleRelease --no-daemon
fi
if [ "$MODE" = "aab" ] || [ "$MODE" = "both" ]; then
  "$GRADLE" bundleRelease --no-daemon
fi

echo "==> Copying artifacts"
mkdir -p "$ROOT/android"
if [ "$MODE" = "apk" ] || [ "$MODE" = "both" ]; then
  cp "$ANDROID/app/build/outputs/apk/release/app-release.apk" "$ROOT/android/flatmate-android.apk"
  echo "APK -> $ROOT/android/flatmate-android.apk"
fi
if [ "$MODE" = "aab" ] || [ "$MODE" = "both" ]; then
  cp "$ANDROID/app/build/outputs/bundle/release/app-release.aab" "$ROOT/android/flatmate-playstore.aab"
  echo "AAB -> $ROOT/android/flatmate-playstore.aab"
fi

# If deployed to S3/CloudFront, push the APK (run after `aws s3 sync dist/ --delete`
# so the APK isn't deleted by the --delete flag).
if [ -n "${FLATMATE_DEPLOY:-}" ] && { [ "$MODE" = "apk" ] || [ "$MODE" = "both" ]; }; then
  if [ -n "${FLATMATE_BUCKET:-}" ] && command -v aws >/dev/null; then
    echo "==> Uploading APK to S3"
    aws s3 cp "$ROOT/android/flatmate-android.apk" \
      "s3://$FLATMATE_BUCKET/downloads/flatmate-android.apk" \
      --content-type application/vnd.android.package-archive \
      --content-disposition attachment --quiet
    if [ -n "${FLATMATE_DISTRIBUTION:-}" ]; then
      aws cloudfront create-invalidation --distribution-id "$FLATMATE_DISTRIBUTION" --paths "/*" >/dev/null
    fi
    echo "APK upload done."
  fi
fi

echo "==> Done."
