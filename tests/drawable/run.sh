#!/usr/bin/env bash
# Host test for the patched Winlator Drawable (copy-on-write for read-only shared buffers, bounds
# checks). Compiles Winlator's real drawable.c for the host and runs DrawableTest against it.
# Usage: tests/drawable/run.sh [path to patched winlator-app]   (default: build/winlator-app from build.sh)
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
W=$(cd "${1:-$HERE/../../build/winlator-app}" && pwd)/app/src/main
OUT=$(mktemp -d)
mkdir -p "$OUT/src/com/winlator/xserver" "$OUT/src/com/winlator/core" "$OUT/src/com/winlator/math" "$OUT/classes"
cp "$W"/java/com/winlator/xserver/{Drawable,XResource,Visual,GraphicsContext}.java "$OUT/src/com/winlator/xserver/"
cp "$W/java/com/winlator/core/Callback.java" "$OUT/src/com/winlator/core/"
cp "$W/java/com/winlator/math/Mathf.java" "$OUT/src/com/winlator/math/"
cp -r "$HERE/stubs/." "$OUT/src/"
cp "$HERE/DrawableTest.java" "$OUT/src/com/winlator/xserver/"
JH=$(dirname "$(dirname "$(readlink -f "$(command -v javac)")")")
gcc -O2 -shared -fPIC -I"$JH/include" -I"$JH/include/linux" -I"$HERE/native" -o "$OUT/classes/libwinlator.so" "$W/cpp/winlator/src/drawable.c"
javac -d "$OUT/classes" $(find "$OUT/src" -name '*.java')
java -Djava.library.path="$OUT/classes" -cp "$OUT/classes" com.winlator.xserver.DrawableTest
