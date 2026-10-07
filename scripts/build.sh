#!/usr/bin/env bash
# Build Kart64 from scratch: upstream SpaghettiKart at the pinned commit, plus
# patches/, compiled to WebAssembly with emsdk. Idempotent — re-run after
# changing a patch or the page and it rebuilds only what changed.
#
#   WORK=~/kart64-work scripts/build.sh
#
# Output: $WORK/SpaghettiKart/build/emscripten with Spaghettify.{js,wasm,data},
# spaghetti.o2r and the page. Serve it with scripts/serve.py.
set -euo pipefail

WORK=${WORK:-$HOME}
SPAGHETTI_COMMIT=aedcf9ada627f4f8e861f12d8b48f587de521e6b
EMSDK_VERSION=${EMSDK_VERSION:-6.0.3}
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$WORK/SpaghettiKart/build/emscripten"
JOBS=${JOBS:-$(getconf _NPROCESSORS_ONLN)}

# --- emsdk -------------------------------------------------------------------
# Pin the version. `emsdk install latest` resolves against the emsdk checkout's
# own release manifest, so a stale clone silently installs an old toolchain.
if [ ! -d "$WORK/emsdk" ]; then
  git clone https://github.com/emscripten-core/emsdk.git "$WORK/emsdk"
else
  git -C "$WORK/emsdk" pull --ff-only || true   # refresh the release manifest
fi
"$WORK/emsdk/emsdk" install "$EMSDK_VERSION"
"$WORK/emsdk/emsdk" activate "$EMSDK_VERSION"
# shellcheck disable=SC1091
source "$WORK/emsdk/emsdk_env.sh"
emcc --version | head -1

# --- ports -------------------------------------------------------------------
embuilder build sdl2 zlib ogg
embuilder build vorbis   # separate: needs ogg's headers already installed

# --- SpaghettiKart + patches -------------------------------------------------
if [ ! -d "$WORK/SpaghettiKart" ]; then
  git clone --recursive https://github.com/HarbourMasters/SpaghettiKart.git "$WORK/SpaghettiKart"
  git -C "$WORK/SpaghettiKart" checkout "$SPAGHETTI_COMMIT"
  git -C "$WORK/SpaghettiKart" submodule update --init --recursive
fi
cd "$WORK/SpaghettiKart"

apply_patch() { # apply_patch <dir> <patch>; tolerate an already-patched tree
  if git -C "$1" apply --check "$2" 2>/dev/null; then
    git -C "$1" apply "$2"
    echo "applied $(basename "$2")"
  elif git -C "$1" apply --check --reverse "$2" 2>/dev/null; then
    echo "skipped $(basename "$2") (already applied)"
  else
    echo "!! $(basename "$2") neither applies nor is already applied." >&2
    echo "   The tree at $1 has other changes. Reset it (git checkout -- . && git clean -fd) and retry." >&2
    exit 1
  fi
}
apply_patch . "$REPO_ROOT/patches/spaghettikart-emscripten.patch"
apply_patch libultraship "$REPO_ROOT/patches/libultraship-emscripten.patch"

# --- configure + build -------------------------------------------------------
# The prefix map keeps local build paths out of the shipped wasm, where
# __FILE__ in asserts and log calls would otherwise embed them. It goes in
# EMCC_CFLAGS because Torch overwrites CMAKE_CXX_FLAGS for itself and yaml-cpp.
export EMCC_CFLAGS="-ffile-prefix-map=$WORK=."
emcmake cmake -S . -B build/emscripten -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DUSE_OPENGLES=ON
cmake --build build/emscripten -j"$JOBS"

# --- engine assets -----------------------------------------------------------
# spaghetti.o2r is the PORT's own asset archive (packed from assets/, nothing
# ROM-derived). It is NOT built by the default target, and index.html hard-fails
# with "spaghetti.o2r: HTTP 404" without it — extraction never starts.
cmake --build build/emscripten --target GenerateO2R

# --- web page ----------------------------------------------------------------
cp "$REPO_ROOT"/web/* "$BUILD_DIR/"

cat <<EOF

Build complete: $BUILD_DIR
  Spaghettify.{js,wasm,data}, spaghetti.o2r, index.html

Serve it:
  python3 $REPO_ROOT/scripts/serve.py $BUILD_DIR 8099

Deploy it:
  $REPO_ROOT/scripts/make-dist.sh $BUILD_DIR dist

Optional, for development without re-extracting per browser profile:
  cp <your-rom>.z64 $WORK/SpaghettiKart/baserom.us.z64
  cmake --build $BUILD_DIR --target ExtractAssets   # writes mk64.o2r
then open http://localhost:8099/?prebuilt  (localhost only, never deployed).

NOTE: ExtractAssets regenerates ROM-derived headers under include/assets/.
Regenerate patches with scripts/regen-patches.sh, never a bare 'git diff'.
EOF
