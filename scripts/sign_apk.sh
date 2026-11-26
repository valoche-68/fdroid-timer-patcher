#!/usr/bin/env bash
# Signe un APK release non signé avec la clé du patcher et vérifie le certificat.
# Usage : scripts/sign_apk.sh <apk-non-signe> <apk-signe-sortie>
# Env   : KEY_JKS (base64), ALIAS, ANDROID_KEY_PASSWORD, ANDROID_STORE_PASSWORD,
#         EXPECTED_CERT_SHA256 (optionnel, empreinte attendue sans ':' en minuscules)
set -euo pipefail

IN="${1:?apk non signé}"
OUT="${2:?apk signé}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

for var in KEY_JKS ALIAS ANDROID_KEY_PASSWORD ANDROID_STORE_PASSWORD; do
  if [ -z "${!var:-}" ]; then
    echo "ERREUR : secret GitHub Actions manquant : $var" >&2
    exit 1
  fi
done

SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
BT="$(ls -d "$SDK"/build-tools/*/ | sort -V | tail -n 1)"
echo "build-tools : $BT"

KS_DIR="$(mktemp -d)"
trap 'rm -rf "$KS_DIR"' EXIT
printf "%s" "$KEY_JKS" | base64 -d > "$KS_DIR/key.jks"
chmod 600 "$KS_DIR/key.jks"

ALIGNED="$KS_DIR/aligned.apk"
"$BT/zipalign" -f -p 4 "$IN" "$ALIGNED"

"$BT/apksigner" sign \
  --ks "$KS_DIR/key.jks" \
  --ks-key-alias "$ALIAS" \
  --ks-pass env:ANDROID_STORE_PASSWORD \
  --key-pass env:ANDROID_KEY_PASSWORD \
  --v4-signing-enabled false \
  --out "$OUT" \
  "$ALIGNED"

CERTS="$("$BT/apksigner" verify --verbose --print-certs "$OUT" 2>&1)"
echo "$CERTS"
if [ -n "${EXPECTED_CERT_SHA256:-}" ]; then
  GOT="$(echo "$CERTS" | grep -i -E 'SHA-?256' | grep -Eo '[0-9a-fA-F]{64}|([0-9a-fA-F]{2}:){31}[0-9a-fA-F]{2}' | tr -d ':' | tr '[:upper:]' '[:lower:]' | head -n 1 || true)"
  if [ "$GOT" != "$EXPECTED_CERT_SHA256" ]; then
    echo "ERREUR : certificat inattendu ('$GOT' != '$EXPECTED_CERT_SHA256')" >&2
    exit 1
  fi
  echo "Certificat de signature conforme ($GOT)."
fi
