#!/usr/bin/env bash
# Empacota a solução do fluxo no zip que o Power Automate importa.
# Uso: flows/build.sh   →   dist/CDIORelatorioArea_1_2_0_0.zip
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
src="$root/flows/CDIORelatorioArea"
ver="$(grep -oP '(?<=<Version>)[^<]+' "$src/solution.xml" | tr '.' '_')"
out="$root/dist/CDIORelatorioArea_${ver}.zip"
mkdir -p "$root/dist"
rm -f "$out"
( cd "$src" && zip -q -r -X "$out" '[Content_Types].xml' solution.xml customizations.xml Workflows )
echo "$out"
