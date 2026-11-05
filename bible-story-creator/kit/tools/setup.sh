#!/usr/bin/env bash
# Creates a new video project:   bash <kit>/tools/setup.sh <project_dir>
# Works on Windows (Git Bash), macOS and Linux. Uses the vendored three.js + toon.ts in <kit>/vendor (offline);
# only if those are missing does it try npm / GitHub. Needs: node >= 22.6, python3 + numpy + Pillow, ffmpeg,
# Playwright + Chromium (global npm install is fine; render.mjs finds it without symlinks).
set -e
KIT="$(cd "$(dirname "$0")/.." && pwd)"; P="${1:?project dir}"
mkdir -p "$P/web/lib" "$P/work" "$P/stills" "$P/out"
P="$(cd "$P" && pwd)"
TMPD="$(mktemp -d 2>/dev/null || echo "$P/.tmp")"; mkdir -p "$TMPD"
cp "$KIT"/engine/*.js "$KIT"/engine/index.html "$P/web/"
cp "$KIT"/example/soldier/story.js "$P/web/story.js"        # starting point: rewrite for the new story
cp "$KIT"/example/soldier/audio.py "$P/audio.py"            # starting point: rewrite music + cue table
cp "$KIT"/tools/*.mjs "$KIT"/tools/*.py "$KIT"/tools/finish.sh "$P/"
# three.js r160 (module build): vendored -> npm -> sparse git clone
if [ -f "$KIT/vendor/three.module.js" ]; then cp "$KIT/vendor/three.module.js" "$P/web/lib/"
elif ( cd "$TMPD" && npm pack three@0.160.0 >/dev/null 2>&1 && tar xzf three-0.160.0.tgz && cp package/build/three.module.js "$P/web/lib/" ); then :
else ( cd "$TMPD" && git clone -q --depth 1 --filter=blob:none --sparse --branch r160 https://github.com/mrdoob/three.js t3 && cd t3 && git sparse-checkout set build && cp build/three.module.js "$P/web/lib/" ); fi
# toon base: the Pen / head / face library from mromidev/claude-animated-shorts (MIT), types stripped by Node 22.6+
TOON="$KIT/vendor/toon.ts"
if [ ! -f "$TOON" ]; then git clone -q --depth 1 https://github.com/mromidev/claude-animated-shorts "$TMPD/cas" && TOON="$TMPD/cas/templates/bridge/toon.ts"; fi
( cd "$P/web" && TOON_SRC="$TOON" node -e "const m=require('node:module'),fs=require('fs');fs.writeFileSync('toonbase.js',m.stripTypeScriptTypes(fs.readFileSync(process.env.TOON_SRC,'utf8'),{mode:'transform'}))" )
cat "$P/web/toonbase.js" "$P/web/roman.js" "$P/web/biblical.js" > "$P/web/toon.js"
rm -rf "$TMPD" 2>/dev/null || true
echo "ready: $P"
echo "after editing cast code run (in the project):  cat web/toonbase.js web/roman.js web/biblical.js > web/toon.js"
