#!/usr/bin/env bash
# Régénère le patch à partir d'un clone local de travail (tag officiel + modifications non commitées).
# Usage : scripts/regen_patch.sh <dossier-du-clone-de-travail>
set -euo pipefail

SRC="${1:?Usage: $0 <dossier-du-clone-de-travail>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$(ls "$ROOT"/patches/*.patch 2>/dev/null | head -n 1)"
OUT="${OUT:-$ROOT/patches/timer.patch}"

git -C "$SRC" add -A
git -C "$SRC" diff --cached --binary > "$OUT"
git -C "$SRC" reset -q
echo "Patch régénéré : $OUT ($(grep -c '^diff --git' "$OUT") fichiers)"
