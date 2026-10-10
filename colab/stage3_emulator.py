# Colab stage 3: try to boot an Android emulator (no KVM on Colab -> software CPU emulation),
# install the Roblox Studio Mobile APK from the GitHub repo and screenshot it.
# Progress: /content/emu.log, screenshots: /content/emu_shots/NN.png
import subprocess

APK_URL = "https://media.githubusercontent.com/media/ArtinMFar/RobloxStudioMobile/ccr-2bf8299c-iiiaw0/apk/RobloxStudioMobile.apk"

EMU = r'''#!/bin/bash
exec > /content/emu.log 2>&1
set -x
nproc; free -g; ls -la /dev/kvm
export ANDROID_HOME=/content/sdk ANDROID_SDK_ROOT=/content/sdk
mkdir -p $ANDROID_HOME && cd $ANDROID_HOME
wget -q https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip -O clt.zip
unzip -q -o clt.zip && mkdir -p cmdline-tools/latest
for f in bin lib NOTICE.txt source.properties; do mv cmdline-tools/$f cmdline-tools/latest/; done
SDKM=$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager
yes | $SDKM --licenses > /dev/null
$SDKM "emulator" "platform-tools" "system-images;android-30;google_apis;x86_64" > /content/sdk-install.log 2>&1
echo no | $ANDROID_HOME/cmdline-tools/latest/bin/avdmanager create avd -n studio -k "system-images;android-30;google_apis;x86_64" -d pixel_5
export PATH=$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH
wget -q "__APK_URL__" -O /content/app.apk; ls -la /content/app.apk
CORES=$(nproc)
emulator -avd studio -no-window -no-audio -no-snapshot -no-boot-anim -gpu swiftshader_indirect \
  -accel off -memory 6144 -cores $CORES -partition-size 8192 > /content/emulator.log 2>&1 &
EMU_PID=$!
mkdir -p /content/emu_shots
adb wait-for-device
for i in $(seq 1 120); do
  if ! kill -0 $EMU_PID 2>/dev/null; then echo "EMULATOR EXITED"; tail -30 /content/emulator.log; exit 1; fi
  B=$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')
  echo "boot check $i: '$B'"
  [ "$B" = "1" ] && break
  sleep 30
done
echo BOOTED
adb install -g /content/app.apk
adb shell am start -n com.winlator/com.winlator.studio.StudioLauncherActivity
for i in $(seq -w 1 90); do
  sleep 40
  adb exec-out screencap -p > /content/emu_shots/$i.png
  adb shell dumpsys activity activities | grep -m2 -E "mResumedActivity|topResumedActivity"
done
echo EMU_DONE
'''.replace("__APK_URL__", APK_URL)

open("/content/emu.sh", "w").write(EMU)
subprocess.Popen(["bash", "-c", "nohup bash /content/emu.sh >/dev/null 2>&1 &"])
print("stage3 launched")
