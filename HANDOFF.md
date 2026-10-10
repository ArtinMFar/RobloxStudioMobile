# Hand-off notes (for continuing in a new session)

Everything needed to rebuild and change the APK is in this repo. The app is
[winlator-app](https://github.com/brunodev85/winlator-app) (LGPL-2.1) at a pinned commit plus
`patches/0001-roblox-studio-launcher.patch`; `build.sh` reconstructs the exact source tree and builds it.
Work happens on branch `ccr-2bf8299c-iiiaw0`.

## Repo layout

| Path | What |
|---|---|
| `patches/0001-roblox-studio-launcher.patch` | All changes to Winlator (new files appear in full). |
| `build.sh` | Fetches winlator-app at `WINLATOR_APP_COMMIT`, applies the patch, runs `assembleRelease`, copies the APK to `apk/`. |
| `gradle/maven-mirror.gradle` | Gradle init script: Maven Central via Google's mirror (repo.maven.apache.org answers HTTP 429 on some cloud machines). |
| `apk/RobloxStudioMobile.apk` | Current signed build (Git LFS). |
| `tests/drawable/` | Host test: compiles Winlator's real `drawable.c` + patched `Drawable.java`, checks the X server drawing fixes. |
| `colab/` | Colab scripts used for testing Studio under Wine (stage 1–5). |
| `docs/` | Screenshot of Studio under Wine on Colab. |

## Rebuilding

Requirements: JDK 17+ (21 works), Android SDK with
`platforms;android-35`, `build-tools;35.0.0`, `platform-tools`, `ndk;24.0.8215888`, `cmake;3.22.1`.

```bash
# SDK (if missing): download commandlinetools from dl.google.com, then
sdkmanager "platforms;android-35" "build-tools;35.0.0" "platform-tools" "ndk;24.0.8215888" "cmake;3.22.1"

# Signing (optional): keystore.properties next to build.sh (git-ignored)
#   storeFile=/abs/path/robloxstudiomobile-release.jks
#   storePassword=...   keyAlias=robloxstudiomobile   keyPassword=...
ANDROID_HOME=/path/to/sdk ./build.sh
```

**Signing key:** the keystore and its password are *not* in the repo. The owner has
`robloxstudiomobile-release.jks` and `SIGNING-PASSWORD.txt`; upload them to the new session to sign
updates with the same key (certificate SHA-256 `f7e1905e…4c1e69`). A different key means the phone
must uninstall the old app first (and re-download Studio).

## Making a change

```bash
./build.sh                                  # creates build/winlator-app with the patch applied
# edit files under build/winlator-app/app/src/main/...
# bump versionCode/versionName in build/winlator-app/app/build.gradle (now 40 / 11.2-studio8)
git -C build/winlator-app add -N .          # include new files in the diff
git -C build/winlator-app diff > patches/0001-roblox-studio-launcher.patch
./build.sh                                  # rebuild from the patch to be sure it applies cleanly
tests/drawable/run.sh                       # if X server drawing code changed
# then: update README version + SHA-256, commit apk/ (LFS) and patch, push
```

## Architecture (what the patch adds/changes)

- `studio/StudioLauncherActivity` – launcher: rootfs install → "Roblox Studio" container (DXVK, Turnip on
  Adreno, Box64 CONSERVATIVE) → download/update Studio → start `RobloxStudioBeta.exe`. Handles
  `roblox-studio-auth:` links (browser login) and the "Save crash report" button.
- `studio/StudioInstaller` – Roblox CDN download (`clientsettingscdn` version → `rbxPkgManifest.txt`,
  package→folder map read from `RobloxStudioInstaller.exe`), MD5 check, safe unzip (folder markers `\`).
- `studio/StudioAuthCallback` – login callback is too long for WinHandler's 256-byte exec packet, so the
  command goes into `C:\windows\temp\roblox-studio-auth.bat`, run with `cmd.exe /c`.
- `studio/Diagnostics`, `studio/TombstoneDecoder` – crash report: Android exit reasons (native tombstones
  decoded from protobuf), Java crash trace, Wine/Box64 output (WINEDEBUG=-all,err+all for the Studio
  container), Roblox Studio logs → `Download/RobloxStudioMobile-report.txt`.
- X server fixes (Winlator bugs Studio triggers):
  - `XInputExtension`: XInput 1 `ListInputDevices` implemented (was BadImplementation → Xlib killed
    the Wine desktop process; Qt's tablet probe triggers it).
  - `Drawable` / `MITSHMExtension` / `DRI3Extension` / `SHMSegmentManager` / `SysVSharedMemory`:
    copy-on-write for read-only client buffers, borrowers moved off a segment before unmap, refcounted
    SHM mappings, `drawImage`/`copyArea`/`getImage`/1-bit/cursor drawing clipped to both buffers,
    GPU stride only while pixels are in the GPU buffer.
  - `DrawRequests.copyArea` + `GLRenderer`: a CopyArea from an offscreen GPU window (Direct3D/Vulkan
    child window) into *part* of a window is drawn as a positioned overlay instead of replacing and
    stretching the whole window's texture (Studio has several D3D child windows).
  - `gpu_image.c`: failed `AHardwareBuffer_lock` no longer returns a garbage pointer.
- `WinHandler`: requests that don't fit are refused; send/receive threads catch exceptions;
  `FileUtils.openIntent` sanitizes URLs and doesn't crash if no app can open them.
- `AppUtils.restartApplication`: `killProcess` instead of `Runtime.exit` (exit-time SIGSEGV).
- `XServerDisplayActivity`: `exec_args` extra, `onNewIntent` exec into the running session,
  session-running flag, session log.

## History (tested on Galaxy S25 Ultra SM-S938B, Snapdragon 8 Elite / Adreno 830, Android 16)

| Version | Fix | Root cause (from the in-app crash report) |
|---|---|---|
| studio2 | unzip of folder markers | "Bad entry in ApplicationConfig.zip: /" |
| studio4 | XInput ListInputDevices | X error killed Wine's desktop process |
| studio5 | read-only SHM copy-on-write | SEGV_ACCERR writing a read-only MIT-SHM mapping |
| studio6 | login callback via batch file | BufferOverflowException in WinHandler.exec |
| studio7 | CopyArea source clipping | SEGV_ACCERR reading past a source buffer |
| studio8 | GPU child windows as overlays | top bar (1280×29 D3D window) stretched over the whole Studio window, flickering with the start page |

State at studio7: Studio starts, browser login works (user signed in), plugins load; the main window
was garbled by the stretching bug fixed in studio8 (not yet confirmed on the device).

## Testing without the phone

- `tests/drawable/run.sh [winlator-app dir] [mode]` – 26 checks; modes `old-behaviour` / `old-copyarea`
  reproduce the original SIGSEGVs.
- Colab (`colab/`): needs the owner's Google sign-in (gcloud ADC with the `colaboratory` scope, see the
  colab-operator skill). Colab has no KVM: the Android emulator can't start the app (10 s start timeout),
  but Studio itself runs under Wine 11 there (`stage1`/`stage2`), and `stage5_auth.py` checks the login
  hand-off with Wine's `cmd.exe`.
