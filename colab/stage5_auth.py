# Colab stage 5: verify the app's roblox-studio-auth batch hand-off with Wine's real cmd.exe.
# A) quoting: the batch runs a stand-in "RobloxStudioBeta.exe" that records its arguments.
# B) forwarding: real Studio running, callback (fake code, real state) sent through the same batch.
import subprocess, base64
open("/content/test.bat", "wb").write(base64.b64decode("QGVjaG8gb2ZmDQoiQzpcUHJvZ3JhbSBGaWxlc1xSb2Jsb3ggU3R1ZGlvXFJvYmxveFN0dWRpb0JldGEuZXhlIiAicm9ibG94LXN0dWRpby1hdXRoOi8/Y29kZT1BYkNfMTIteCUlMkZ5JSUzRCUlMjV6JnN0YXRlPWV5SndhV1FpT2lJeU9EZ2lMQ0psZG1WdWRGOW9ZVzVrYkdWeVgyNWhiV1VpT2lKRmVIUmxjbTVoYkV4dloybHVSbXh2ZHlKOSUlM0QmZXh0cmE9YStiIWNeZCINCg=="))
open("/content/expected.txt", "wb").write(base64.b64decode("cm9ibG94LXN0dWRpby1hdXRoOi8/Y29kZT1BYkNfMTIteCUyRnklM0QlMjV6JnN0YXRlPWV5SndhV1FpT2lJeU9EZ2lMQ0psZG1WdWRGOW9ZVzVrYkdWeVgyNWhiV1VpT2lKRmVIUmxjbTVoYkV4dloybHVSbXh2ZHlKOSUzRCZleHRyYT1hK2IhY15k"))
open("/content/printargs.c", "w").write(r'''
#include <stdio.h>
int main(int argc, char **argv) {
    FILE *f = fopen("Z:\\content\\args.txt", "wb");
    for (int i = 1; i < argc; i++) fprintf(f, "%s", argv[i]);
    fclose(f);
    return 0;
}
''')
open("/content/stage5.sh", "w").write(r'''#!/bin/bash
exec > /content/stage5.log 2>&1
set -x
export DEBIAN_FRONTEND=noninteractive
dpkg --add-architecture i386
mkdir -pm755 /etc/apt/keyrings
wget -qO /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key
wget -qNP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/noble/winehq-noble.sources
apt-get update -qq
apt-get install -y -qq --install-recommends winehq-stable > /dev/null 2>&1
apt-get install -y -qq xvfb x11-utils imagemagick xdotool gcc-mingw-w64-x86-64 > /dev/null 2>&1
x86_64-w64-mingw32-gcc -O2 -o /content/printargs.exe /content/printargs.c
export DISPLAY=:99
Xvfb :99 -screen 0 1600x900x24 -noreset &
sleep 3
export WINEDEBUG=-all WINEDLLOVERRIDES="mscoree,mshtml="

echo "=== A: quoting test ==="
export WINEPREFIX=/root/pfx2
wineboot -i; wineserver -w
mkdir -p "$WINEPREFIX/drive_c/Program Files/Roblox Studio" "$WINEPREFIX/drive_c/windows/temp"
cp /content/printargs.exe "$WINEPREFIX/drive_c/Program Files/Roblox Studio/RobloxStudioBeta.exe"
cp /content/test.bat "$WINEPREFIX/drive_c/windows/temp/roblox-studio-auth.bat"
rm -f /content/args.txt
wine "C:\windows\system32\cmd.exe" /c "C:\windows\temp\roblox-studio-auth.bat"
wineserver -w
echo "expected: $(cat /content/expected.txt)"
echo "received: $(cat /content/args.txt)"
cmp /content/expected.txt /content/args.txt && echo QUOTING_OK || echo QUOTING_MISMATCH

echo "=== B: forwarding test with real Studio ==="
python3 -I /content/fetch_studio.py /content/studio > /content/fetch.log 2>&1
cat > /content/logurl.sh <<'EOS'
#!/bin/bash
printf '%s\n' "$@" >> /content/browser_calls.txt
EOS
chmod +x /content/logurl.sh
export WINEPREFIX=/root/pfx
wineboot -i; wineserver -w
wine reg add "HKCU\Software\Wine\WineBrowser" /v Browsers /d /content/logurl.sh /f
wine reg add "HKCU\Software\Wine" /v Version /d win10 /f
wineserver -w
STUDIO="$WINEPREFIX/drive_c/Program Files/Roblox Studio"
rm -rf "$STUDIO"; cp -r /content/studio "$STUDIO"
cd "$STUDIO"
wine RobloxStudioBeta.exe > /content/studio_stdout.log 2>&1 &
sleep 150
xdotool mousemove 775 500 click 1
sleep 20
cat /content/browser_calls.txt
python3 -I /content/make_callback.py
mkdir -p "$WINEPREFIX/drive_c/windows/temp"
cp /content/callback.bat "$WINEPREFIX/drive_c/windows/temp/roblox-studio-auth.bat"
date -u +%H:%M:%S > /content/callback_time.txt
wine "C:\windows\system32\cmd.exe" /c "C:\windows\temp\roblox-studio-auth.bat"
sleep 25
import -window root /content/after_callback.png
L=$(ls -t "$WINEPREFIX"/drive_c/users/root/AppData/Local/Roblox/logs/*Studio*.log | head -1)
echo "studio logs:"; ls -la "$WINEPREFIX"/drive_c/users/root/AppData/Local/Roblox/logs/
grep -n -iE "auth|oauth|ExternalLogin|callback|redirect|token|login" "$L" | cut -c1-260 | tail -40
echo STAGE5_DONE
''')
open("/content/make_callback.py", "w").write(r'''
# Same transformation as StudioAuthCallback.batchContent(), with a fake code and the real state.
import urllib.parse
url = open("/content/browser_calls.txt").read().strip().splitlines()[-1]
state = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["state"][0]
uri = "roblox-studio-auth:/?code=FAKE-CODE-FOR-TEST&state=" + urllib.parse.quote(state, safe="")
arg = uri.replace('"', "%22").replace("%", "%%")
open("/content/callback.bat", "w", newline="").write('@echo off\r\n"C:\\Program Files\\Roblox Studio\\RobloxStudioBeta.exe" "' + arg + '"\r\n')
print("callback uri:", uri)
''')
subprocess.Popen(["bash", "-c", "nohup bash /content/stage5.sh >/dev/null 2>&1 &"])
print("stage5 launched")
