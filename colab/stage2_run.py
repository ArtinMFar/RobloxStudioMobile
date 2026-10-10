# Colab stage 2: start a virtual X display, create a Wine prefix, launch Roblox
# Studio and take a screenshot every 20 seconds (/content/shots/NN.png).
import subprocess

RUN = r'''#!/bin/bash
exec > /content/run.log 2>&1
set -x
wine --version
export DISPLAY=:99
Xvfb :99 -screen 0 1600x900x24 +extension GLX +render -noreset &
sleep 3
glxinfo -B | head -20
export WINEPREFIX=/root/pfx
export WINEDEBUG=-all,err+module
export WINEDLLOVERRIDES="dxdiagn,winemenubuilder.exe,mscoree,mshtml="
export WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS="--in-process-gpu --use-angle=gl"
export WINE_D3D_CONFIG="renderer=gl"
wineboot -i
wineserver -w
wine reg add "HKCU\\Software\\Wine" /v Version /d win10 /f
wineserver -w
STUDIO="$WINEPREFIX/drive_c/Program Files/Roblox Studio"
rm -rf "$STUDIO"; cp -r /content/studio "$STUDIO"
mkdir -p /content/shots
cd "$STUDIO"
wine RobloxStudioBeta.exe > /content/studio.log 2>&1 &
for i in $(seq -w 1 45); do
  sleep 20
  import -window root /content/shots/$i.png
  xwininfo -root -tree | grep -E '^\s+0x' | grep -v 'has no name' | head -8
done
echo RUN_DONE
'''

open("/content/run.sh", "w").write(RUN)
subprocess.Popen(["bash", "-c", "nohup bash /content/run.sh >/dev/null 2>&1 &"])
print("stage2 launched")
