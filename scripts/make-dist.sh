#!/usr/bin/env bash
# Assemble the deployable folder from a build directory — by whitelist, so
# nothing ROM-derived can ride along. Refuses to finish if any forbidden file
# would end up in the dist.
#
#   scripts/make-dist.sh <buildDir> [distDir]     (distDir defaults to ./dist)
set -euo pipefail

BUILD=${1:?usage: make-dist.sh <buildDir> [distDir]}
DIST=${2:-dist}

# Everything a browser needs, and nothing else.
FILES=(
  Spaghettify.js Spaghettify.wasm Spaghettify.data
  spaghetti.o2r
  index.html coi-sw.js manifest.webmanifest
  icon-192.png icon-512.png apple-touch-icon.png
  courses.json
  courses/silverstone/silverstone-v1.9.o2r
  courses/silverstone/media/index.html
  courses/silverstone/media/manifest.json
  courses/silverstone/media/silverstone-mario-full-lap.mp4
  courses/silverstone/media/silverstone-verstappen-vs-mario.mp4
  courses/silverstone/media/comparison-poster.webp
  courses/silverstone/media/comparison-sync.json
)

for f in "${FILES[@]}"; do
  [ -f "$BUILD/$f" ] || { echo "!! missing $BUILD/$f (did the build finish, including GenerateO2R?)" >&2; exit 1; }
done

rm -rf "$DIST" && mkdir -p "$DIST"
for f in "${FILES[@]}"; do
  mkdir -p "$DIST/$(dirname "$f")"
  cp "$BUILD/$f" "$DIST/$f"
done

# The gallery screenshots, as a folder.
cp -R "$BUILD/courses/silverstone/media/screenshots" "$DIST/courses/silverstone/media/"

# Belt and braces: even though the copy is a whitelist, assert the result.
bad=$(find "$DIST" -type f \( -iname 'mk64*' -o -iname '*.z64' -o -iname '*.v64' -o -iname '*.n64' -o -iname 'baserom*' \) | head)
if [ -n "$bad" ]; then
  echo "!! ROM-derived files in the dist — refusing:" >&2; echo "$bad" >&2; rm -rf "$DIST"; exit 1
fi
if ls "$BUILD"/mk64.o2r* "$BUILD"/baserom* >/dev/null 2>&1; then
  echo "note: $BUILD holds mk64.o2r/baserom (dev extraction). They were NOT copied."
fi

du -sh "$DIST"; ls -la "$DIST"
echo "dist ready: $DIST  (a static site for any HTTPS host)"
