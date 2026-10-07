#!/usr/bin/env bash
# Regenerate patches/ from a patched SpaghettiKart working tree, with an
# explicit pathspec per file. Never a bare `git diff`: the ExtractAssets target
# regenerates ROM-derived headers under include/assets/, and an unquoted or
# missing pathspec once produced an empty patch without erroring.
#
#   scripts/regen-patches.sh [$WORK/SpaghettiKart]
set -euo pipefail

SK=${1:-${WORK:-$HOME}/SpaghettiKart}
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO_ROOT/patches"

SK_FILES=(
  CMakeLists.txt
  cmake/emscripten-deps.cmake
  src/main.c
  src/camera.c
  src/code_80057C60.c
  src/math_util_2.c
  src/menu_items.c
  src/menus.c
  src/render_objects.c
  src/port/Engine.cpp
  src/port/Engine.h
  src/port/Game.cpp
  src/port/GameExtractor.cpp
  src/port/kart64_web.cpp
)
LUS_FILES=(
  CMakeLists.txt
  cmake/dependencies/emscripten.cmake
  include/fast/interpreter.h
  include/ship/audio/SDLAudioPlayer.h
  src/fast/backends/gfx_opengl.cpp
  src/fast/interpreter.cpp
  src/ship/audio/SDLAudioPlayer.cpp
  src/ship/window/gui/Gui.cpp
)

# New files only show in `git diff` once git knows about them.
git -C "$SK" add -N cmake/emscripten-deps.cmake src/port/kart64_web.cpp 2>/dev/null || true
git -C "$SK/libultraship" add -N cmake/dependencies/emscripten.cmake 2>/dev/null || true

git -C "$SK" diff -- "${SK_FILES[@]}" > "$OUT/spaghettikart-emscripten.patch"
git -C "$SK/libultraship" diff -- "${LUS_FILES[@]}" > "$OUT/libultraship-emscripten.patch"

# Anything modified that the lists above do not cover is either a mistake or a
# file that needs adding to the list — say so rather than silently dropping it.
extra=$(git -C "$SK" status --porcelain -- . ':!include/assets' ':!build' | grep -vE "^ M ($(IFS='|'; echo "${SK_FILES[*]}"))$|^ ?[AM]+ cmake/emscripten-deps.cmake$|^ ?[AM]+ src/port/kart64_web.cpp$|^ [mM] libultraship$" || true)
[ -z "$extra" ] || { echo "note: changes outside the patch list (not captured):"; echo "$extra"; }

for p in "$OUT"/*.patch; do
  if grep -qE '^\+\+\+ b/include/assets/|^diff --git a/include/assets' "$p"; then
    echo "!! $p touches include/assets/ (ROM-derived) — refusing." >&2; exit 1
  fi
done
wc -l "$OUT"/*.patch
echo "patches regenerated. Review with: git diff -- patches/"
