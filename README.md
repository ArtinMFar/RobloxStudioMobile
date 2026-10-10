# Roblox Studio Mobile

A personal Android build that runs the **Windows version of Roblox Studio** on an ARM64 phone,
using **Wine** (Windows API layer) and **Box64** (x86-64 → ARM64 translator). It is a small patch
on top of [Winlator](https://github.com/brunodev85/winlator) (LGPL-2.1), which already packages
Wine, Box64, DXVK and the Turnip/Vortek Vulkan drivers into an Android app.

> **Roblox Studio is not included** in this repository or in the APK. The app downloads it from
> Roblox's official deployment servers (`setup.rbxcdn.com`) the first time it starts, exactly like
> Roblox's own installer does, and keeps it updated on later launches.

## What happens when you open the app

1. Installs the Windows environment (Wine + Box64 rootfs bundled with Winlator) — first launch only.
2. Creates a Wine container called "Roblox Studio" (DXVK for Direct3D 11, Turnip on Adreno GPUs
   or Vortek elsewhere, Box64 "Conservative" preset because Studio is heavily multi-threaded).
3. Asks Roblox for the current Studio version, downloads ~575 MB of packages (MD5-verified, ~1.1 GB unpacked)
   and unpacks them into `C:\Program Files\Roblox Studio` using the package → folder map read out of
   the official `RobloxStudioInstaller.exe` (same technique as Vinegar/Bloxstrap).
4. Starts `RobloxStudioBeta.exe` full screen.

After Studio is closed the app shows a launcher screen instead of relaunching it. "Winlator settings
(advanced)" opens the normal Winlator UI for tuning graphics drivers, Box64 presets, etc.

### Logging in

Studio's built-in login window needs Microsoft WebView2, which is not installed (it is very heavy
under Box64), so Studio shows **"Launch Failed … Login via Browser"**. Tap **Login via Browser**:
the login page opens in your Android browser, and when roblox.com redirects to the
`roblox-studio-auth:` link, Android hands it to this app, which passes it to the running Studio —
the same way it works on Windows.

## Requirements / expectations

- 64-bit ARM Android 8+ phone; 6 GB+ RAM and ~3 GB free storage recommended.
- Snapdragon (Adreno) GPUs work best (Turnip Vulkan driver). Others use Vortek and may be slower.
- Studio is a big desktop app: expect slow start-up and modest frame rates.
- The package name must stay `com.winlator` (Winlator's rootfs has that path compiled in), so
  **uninstall the official Winlator first** — the two can't be installed side by side.

## Building

```
ANDROID_HOME=/path/to/sdk ./build.sh
```

`build.sh` fetches `brunodev85/winlator-app` at the pinned commit, applies `patches/`, and runs the
Gradle release build. Put a `keystore.properties` next to the script to get a signed APK (see the
comment at the top of `build.sh`). Keystores and passwords are git-ignored and never committed.

## Colab test

`colab/stage1_setup.py` and `colab/stage2_run.py` install Wine on a Google Colab VM, download Studio
with the same CDN logic as the app, and launch it on a virtual X display. Result with Wine 11.0
(software rendering), Studio 0.742:

![Roblox Studio running under Wine on Colab](docs/colab-studio-screenshot.png)

Colab VMs have no KVM, so they can't run an ARM64 Android emulator at usable speed; this test
covers the Studio-under-Wine part, not the APK itself.

## Changes to Winlator (`patches/0001-roblox-studio-launcher.patch`)

- `studio/StudioLauncherActivity` — new launcher screen and first-run/update flow.
- `studio/StudioInstaller` — Roblox CDN download, MD5 check, safe unzip, staged install.
- `XServerDisplayActivity` — `exec_args` extra, "session running" flag, and `onNewIntent` that runs
  a program in the live session (used for the browser-login callback).
- `RootFSInstaller` — completion callback; `AndroidManifest` — new launcher + `roblox-studio-auth`
  link handler; release signing config read from `keystore.properties`.

## License

The patch is a modification of Winlator and is distributed under the same LGPL-2.1 license.
Wine (LGPL), Box64 (MIT), DXVK (zlib) and Mesa (MIT) keep their own licenses. Roblox and Roblox
Studio are trademarks of Roblox Corporation; this project is not affiliated with Roblox.
