#!/bin/sh
# Builds the WebAssembly module of the RDF check and writes it to ui/pkg/.
# No network is used. Tools: cargo with the target wasm32-unknown-unknown,
# wasm-bindgen CLI 0.2.127 (the same version as the crate wasm-bindgen),
# wasm-opt (optional; without it the module stays larger).
set -eu

HERE="$(cd "$(dirname "$0")" && pwd)"
PKG_ROOT="$(cd "$HERE/.." && pwd)"
CARGO="${CARGO:-cargo}"
export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-$PKG_ROOT/target-wasm}"
OUT="$PKG_ROOT/ui/pkg"
RAW="$CARGO_TARGET_DIR/wasm32-unknown-unknown/release/parlpdfech_rdfcheck.wasm"
BG="$OUT/parlpdfech_rdfcheck_bg.wasm"

cd "$PKG_ROOT"

# 1. Rust to WebAssembly. The profile values below apply to this build only
#    (all crates of the module): small code, one code unit, full link-time
#    optimization, no unwind tables.
export CARGO_PROFILE_RELEASE_OPT_LEVEL="${CARGO_PROFILE_RELEASE_OPT_LEVEL:-z}"
export CARGO_PROFILE_RELEASE_LTO="${CARGO_PROFILE_RELEASE_LTO:-fat}"
export CARGO_PROFILE_RELEASE_CODEGEN_UNITS="${CARGO_PROFILE_RELEASE_CODEGEN_UNITS:-1}"
export CARGO_PROFILE_RELEASE_PANIC="${CARGO_PROFILE_RELEASE_PANIC:-abort}"

# Paths of the build host. Without the next flags the module holds the absolute paths of the source
# files of each crate (in panic messages): the home folder with the name of the user account. The
# flags replace the folder of cargo, the folder of rustup, the package folder and the home folder by
# fixed names. The last flag that fits a path applies, so the home folder comes first.
CARGO_HOME_DIR="${CARGO_HOME:-$HOME/.cargo}"
RUSTUP_HOME_DIR="${RUSTUP_HOME:-$HOME/.rustup}"
REMAP="--remap-path-prefix=$HOME=/build-home --remap-path-prefix=$PKG_ROOT=/package"
REMAP="$REMAP --remap-path-prefix=$CARGO_HOME_DIR=/cargo --remap-path-prefix=$RUSTUP_HOME_DIR=/rustup"
if command -v rustc >/dev/null 2>&1; then
  SYSROOT="$(rustc --print sysroot 2>/dev/null || true)"
  [ -n "$SYSROOT" ] && REMAP="$REMAP --remap-path-prefix=$SYSROOT=/rustup/toolchain"
fi
export RUSTFLAGS="${RUSTFLAGS:-} $REMAP"
"$CARGO" build --offline --locked --release --target wasm32-unknown-unknown -p parlpdfech-rdfcheck

# 2. JavaScript glue for the browser (ES module, no bundler).
mkdir -p "$OUT"
wasm-bindgen --target web --no-typescript --out-dir "$OUT" "$RAW"

# 3. Size optimization.
if command -v wasm-opt >/dev/null 2>&1; then
  wasm-opt -Oz "$BG" -o "$BG.tmp"
  mv "$BG.tmp" "$BG"
else
  echo "wasm-opt is absent: the module is not size-optimized." >&2
fi

# 4. Proof: no path of the build host is in the two files (byte search; a hit stops the build).
#    Searched: the home folder of the user, the package folder, the start of a home folder on macOS
#    and the start /home/.
HITS=0
MAC_HOMES="/$(printf 'Users')/"
for NEEDLE in "$HOME/" "$PKG_ROOT/" "$MAC_HOMES" "/home/"; do
  for F in "$BG" "$OUT/parlpdfech_rdfcheck.js"; do
    N="$(LC_ALL=C grep -a -o -F -e "$NEEDLE" "$F" | wc -l | tr -d ' ')"
    HITS=$((HITS + N))
  done
done
echo "paths of the build host in ui/pkg: $HITS"
if [ "$HITS" -ne 0 ]; then
  echo "ERROR: ui/pkg holds $HITS path strings of the build host." >&2
  exit 1
fi

echo "raw (cargo):      $(wc -c < "$RAW" | tr -d ' ') bytes"
echo "ui/pkg (final):   $(wc -c < "$BG" | tr -d ' ') bytes"
echo "ui/pkg (gzip -9): $(gzip -9 -c "$BG" | wc -c | tr -d ' ') bytes"
