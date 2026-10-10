#!/usr/bin/env bash
# Host test for studio/MinidumpDecoder (crash-dump summary in the in-app report): a synthetic x64
# dump plus, if it can be downloaded, a real Windows dump from Breakpad's test data.
# Usage: tests/minidump/run.sh [path to patched winlator-app]   (default: build/winlator-app from build.sh)
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
W=$(cd "${1:-$HERE/../../build/winlator-app}" && pwd)/app/src/main
OUT=$(mktemp -d)
python3 -I "$HERE/make_dump.py" "$OUT/synthetic.dmp"
REAL=none
if curl -sSfL -o "$OUT/minidump2.dmp" https://raw.githubusercontent.com/google/breakpad/main/src/processor/testdata/minidump2.dmp; then REAL="$OUT/minidump2.dmp"; fi
javac -d "$OUT/classes" "$W/java/com/winlator/studio/MinidumpDecoder.java" "$HERE/DumpTest.java"
java -cp "$OUT/classes" DumpTest "$REAL" "$OUT/synthetic.dmp"
