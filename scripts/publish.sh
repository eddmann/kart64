#!/usr/bin/env bash
# Build locally and publish to GitHub Pages, with no build on GitHub.
#
#   WORK=~/kart64-work scripts/publish.sh              build (incremental), then publish
#   WORK=~/kart64-work scripts/publish.sh --no-build   publish the last build as it is
#
# The build is scripts/build.sh. The site from make-dist.sh then goes to the
# gh-pages branch as a single commit, replacing the last one, and Pages
# serves that branch as it is. Commit first: the site's commit names the
# source commit it was built from.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK=${WORK:-$HOME}
BUILD="$WORK/SpaghettiKart/build/emscripten"

if [ -n "$(git -C "$ROOT" status --porcelain)" ]; then
  echo "!! uncommitted changes: commit first, so the site records what it was built from" >&2
  exit 1
fi
SRC=$(git -C "$ROOT" rev-parse --short HEAD)
REMOTE=$(git -C "$ROOT" remote get-url origin)

if [ "${1:-}" != "--no-build" ]; then
  WORK="$WORK" "$ROOT/scripts/build.sh" >/dev/null   # also copies web/ into the build
else
  cp "$ROOT"/web/* "$BUILD/"
fi

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
"$ROOT/scripts/make-dist.sh" "$BUILD" "$TMP/site" >/dev/null   # whitelist; refuses ROM-derived files
touch "$TMP/site/.nojekyll"                                     # serve the files as they are

git -C "$TMP/site" init -q -b gh-pages
git -C "$TMP/site" add -f -A          # -f: spaghetti.o2r is the port's own archive, not the ROM's
git -C "$TMP/site" commit -q -m "Site built from $SRC"
git -C "$TMP/site" push -q --force "$REMOTE" gh-pages

echo "published $SRC to gh-pages ($(du -sh "$TMP/site" | cut -f1)): GitHub Pages serves it in a minute or so"
