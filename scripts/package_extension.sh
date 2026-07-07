#!/usr/bin/env bash
# Builds the .zip to upload to the Chrome Web Store Developer Dashboard from
# extension/. Output goes to dist/ at the repo root (git-ignored).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ext_dir="$repo_root/extension"
dist_dir="$repo_root/dist"

version="$(python3 -c "import json; print(json.load(open('$ext_dir/manifest.json'))['version'])")"
out_zip="$dist_dir/lolbin-reference-tool-v${version}.zip"

mkdir -p "$dist_dir"
rm -f "$out_zip"

cd "$ext_dir"
zip -r -X "$out_zip" . -x '.*'

echo "Packaged: $out_zip"
unzip -l "$out_zip"
