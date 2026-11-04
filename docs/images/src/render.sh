#!/usr/bin/env bash
# SVG → PNG (headless Edge). Kullanım: bash docs/images/src/render.sh [klasör veya svg ...]
# Edge ilk çalıştırmada bazen boş çıkar; her dosya birkaç kez denenir.
E="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
PROFILE="${TEMP:-/tmp}/inter-labs-edge"
for arg in "${@:-docs/images/detay}"; do
  if [ -d "$arg" ]; then set -- "$arg"/*.svg; else set -- "$arg"; fi
  for f in "$@"; do
    dir=$(cd "$(dirname "$f")" && pwd -W); base=$(basename "$f" .svg)
    w=$(grep -o 'width="[0-9]*"' "$f" | head -1 | tr -dc 0-9); h=$(grep -o 'height="[0-9]*"' "$f" | head -1 | tr -dc 0-9)
    rm -f "$dir/$base.png"
    for i in 1 2 3 4 5; do
      "$E" --headless=new --disable-gpu --no-first-run --user-data-dir="$PROFILE-$RANDOM" --hide-scrollbars \
        --window-size="$w,$h" --screenshot="$dir/$base.png" "file:///$dir/$base.svg" >/dev/null 2>&1
      for _ in 1 2 3 4 5 6 7 8 9 10; do [ -f "$dir/$base.png" ] && break; sleep 0.5; done   # Edge dosyayı geç yazabilir
      [ -f "$dir/$base.png" ] && break
    done
    [ -f "$dir/$base.png" ] && echo "ok $base.png" || echo "HATA $base.png"
  done
done
