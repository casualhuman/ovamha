#!/usr/bin/env bash
# Two Android emulators that receive Ovamha's SMS through the emulator's simulated GSM modem:
#   emulator-5554 = her phone, emulator-5556 = the referral hospital's phone.
# One-time setup: brew install --cask android-commandlinetools, then sdkmanager installs
#   platform-tools, emulator and system-images;android-34;google_apis;arm64-v8a (see docs/demo/sms-demo.md).
# Then run Ovamha with OVAMHA_SMS_EMULATOR=1 (make run-phones does both).
set -euo pipefail
SDK="${ANDROID_SDK_ROOT:-/opt/homebrew/share/android-commandlinetools}"
export ANDROID_SDK_ROOT="$SDK" ANDROID_HOME="$SDK"
JDK="$(cd "$(dirname "$0")/.." && pwd)/tools/jdk-17.0.20.1+1/Contents/Home"
[ -d "$JDK" ] && export JAVA_HOME="${JAVA_HOME:-$JDK}"
"${JAVA_HOME:-/usr}/bin/java" -version 2>&1 | grep -qE 'version "(1[7-9]|2[0-9])' || { echo "Java 17+ needed for avdmanager: set JAVA_HOME (see tools/)"; exit 1; }
IMAGE="system-images;android-34;google_apis;arm64-v8a"
export PATH="$SDK/cmdline-tools/latest/bin:$PATH"
ADB="$SDK/platform-tools/adb"

for name in ovamha-her ovamha-hospital; do
  if ! "$SDK/emulator/emulator" -list-avds | grep -qx "$name"; then
    echo "Creating $name"
    echo no | avdmanager create avd -n "$name" -k "$IMAGE" --force >/dev/null
    # A modern phone screen, with the keyboard on screen.
    printf 'hw.lcd.width=1080\nhw.lcd.height=2400\nhw.lcd.density=420\nhw.keyboard=yes\nhw.gpu.enabled=yes\n' >> "$HOME/.android/avd/$name.avd/config.ini"
  fi
done

start() {  # name port
  if "$ADB" devices | grep -q "emulator-$2"; then echo "$1 already running (emulator-$2)"; return; fi
  echo "Starting $1 on emulator-$2"
  "$SDK/emulator/emulator" -avd "$1" -port "$2" -no-snapshot-save -no-boot-anim -gpu host >/dev/null 2>&1 &
}
start ovamha-her 5554
start ovamha-hospital 5556

for port in 5554 5556; do
  "$ADB" -s "emulator-$port" wait-for-device
  until [ "$("$ADB" -s "emulator-$port" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; do sleep 2; done
  echo "emulator-$port ready"
done
echo "Both phones ready. Start Ovamha with: OVAMHA_SMS_EMULATOR=1 make run"
