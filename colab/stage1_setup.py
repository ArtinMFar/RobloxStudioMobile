# Colab stage 1: install Wine + a virtual X display, then download Roblox Studio
# from Roblox's official CDN and lay it out exactly like the official installer.
# Runs in the background on the VM; progress goes to /content/*.log.
import subprocess, textwrap

FETCH = r'''
import json, os, re, sys, urllib.request, zipfile, io, hashlib
dest = sys.argv[1]
CDN = "https://setup.rbxcdn.com"
def get(url):
    with urllib.request.urlopen(url, timeout=300) as r: return r.read()
ver = json.loads(get("https://clientsettingscdn.roblox.com/v2/client-version/WindowsStudio64"))
guid = ver["clientVersionUpload"]; print("Studio", ver["version"], guid, flush=True)
base = f"{CDN}/channel/common/{guid}-"
inst = get(base + "RobloxStudioInstaller.exe")
pdirs = None
for m in re.finditer(rb'\x00(\{"[^\x00]{20,8000}?"\})\x00', inst):
    try:
        d = json.loads(m.group(1))
        if any(k.endswith(".zip") for k in d): pdirs = d; break
    except Exception: pass
assert pdirs, "package map not found"
lines = get(base + "rbxPkgManifest.txt").decode().split()
assert lines[0] == "v0"
pkgs = [(lines[i], lines[i+1]) for i in range(1, len(lines), 4)]
os.makedirs(dest, exist_ok=True)
for name, md5 in pkgs:
    if name not in pdirs: print("skip", name); continue
    data = get(base + name)
    assert hashlib.md5(data).hexdigest() == md5, name
    sub = pdirs[name].replace("\\", "/")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            fn = info.filename.replace("\\", "/")
            if fn.endswith("/"): continue
            out = os.path.join(dest, sub, fn)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "wb") as f: f.write(z.read(info))
    print("ok", name, len(data), flush=True)
with open(os.path.join(dest, "AppSettings.xml"), "w", newline="") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\r\n<Settings>\r\n        <ContentFolder>content</ContentFolder>\r\n        <BaseUrl>http://www.roblox.com</BaseUrl>\r\n</Settings>\r\n')
print("DONE", flush=True)
'''

SETUP = r'''#!/bin/bash
exec > /content/setup.log 2>&1
set -x
export DEBIAN_FRONTEND=noninteractive
python3 -I /content/fetch_studio.py /content/studio > /content/fetch.log 2>&1 &
dpkg --add-architecture i386
mkdir -pm755 /etc/apt/keyrings
wget -qO /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key
wget -qNP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/noble/winehq-noble.sources
apt-get update -qq
apt-get install -y -qq --install-recommends winehq-stable > /content/apt-wine.log 2>&1
apt-get install -y -qq xvfb x11-utils x11-apps imagemagick xdotool mesa-vulkan-drivers vulkan-tools mesa-utils cabextract unzip > /content/apt-x.log 2>&1
wine --version
wait
echo SETUP_DONE
'''

open("/content/fetch_studio.py", "w").write(FETCH)
open("/content/setup.sh", "w").write(SETUP)
subprocess.Popen(["bash", "-c", "nohup bash /content/setup.sh >/dev/null 2>&1 &"])
print("stage1 launched")
