# Colab stage 3b: retry APK install on the (slow, software-emulated) emulator via push + pm install.
import subprocess

RETRY = r'''#!/bin/bash
exec > /content/install.log 2>&1
set -x
export PATH=/content/sdk/platform-tools:$PATH
until adb shell pm path android | grep -q package; do sleep 20; done
adb push /content/app.apk /data/local/tmp/app.apk
for attempt in 1 2 3 4 5; do
  adb shell pm install -g -t /data/local/tmp/app.apk && break
  sleep 60
done
adb shell pm list packages | grep winlator
adb shell am start -n com.winlator/com.winlator.studio.StudioLauncherActivity
echo INSTALL_STEP_DONE
'''

open("/content/install.sh", "w").write(RETRY)
subprocess.Popen(["bash", "-c", "nohup bash /content/install.sh >/dev/null 2>&1 &"])
print("install retry launched")
