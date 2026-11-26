#!/usr/bin/env bash
# Applique patches/*.patch sur un clone du code officiel.
# Usage : scripts/apply_patch.sh <dossier-du-clone-amont>
set -euo pipefail

SRC="${1:?Usage: $0 <dossier-du-clone-amont>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

shopt -s nullglob
patches=("$ROOT"/patches/*.patch)
if [ ${#patches[@]} -eq 0 ]; then
  echo "ERREUR : aucun patch dans $ROOT/patches" >&2
  exit 1
fi

for p in "${patches[@]}"; do
  echo "==> Application de $(basename "$p")"
  if git -C "$SRC" apply --check --whitespace=nowarn "$p" 2>/dev/null; then
    git -C "$SRC" apply --whitespace=nowarn "$p"
  elif git -C "$SRC" apply --3way --whitespace=nowarn "$p"; then
    # --3way peut laisser des marqueurs de conflit : on refuse dans ce cas.
    if git -C "$SRC" diff --name-only --diff-filter=U | grep -q .; then
      echo "ERREUR : conflits lors de l'application 3-way de $(basename "$p")" >&2
      git -C "$SRC" diff --name-only --diff-filter=U >&2
      exit 1
    fi
  else
    echo "ERREUR : le patch $(basename "$p") ne s'applique plus sur cette version amont." >&2
    echo "Il faut le régénérer (voir README, section « Mettre à jour le patch »)." >&2
    exit 1
  fi
done
echo "Patch(s) appliqué(s) avec succès."
