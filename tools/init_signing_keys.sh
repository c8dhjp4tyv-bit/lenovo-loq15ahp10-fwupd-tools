#!/bin/sh
set -eu

# Creates a long-lived root CA and a shorter-lived release-signing certificate.
# The private keys stay outside the repository and are never copied by the
# remote build script.
DEFAULT_KEY_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/loq15ahp10-fwupd-tools/keys"
KEY_ROOT=${1:-$DEFAULT_KEY_ROOT}
PRIVATE_DIR="$KEY_ROOT/private"
PUBLIC_DIR="$KEY_ROOT/public"

if [ -e "$PRIVATE_DIR/loq-community-root-ca.key" ] || \
   [ -e "$PRIVATE_DIR/loq-community-release-signer.key" ] || \
   [ -e "$PUBLIC_DIR/loq-community-root-ca.pem" ] || \
   [ -e "$PUBLIC_DIR/loq-community-release-signer.pem" ]; then
    echo "signing keys already exist under $KEY_ROOT; refusing to replace them" >&2
    exit 1
fi

umask 077
install -d -m 0700 "$PRIVATE_DIR" "$PUBLIC_DIR"

openssl req -x509 -newkey rsa:4096 -nodes -sha256 \
    -keyout "$PRIVATE_DIR/loq-community-root-ca.key" \
    -out "$PUBLIC_DIR/loq-community-root-ca.pem" \
    -days 3650 \
    -subj '/O=LOQ 15AHP10 Community/CN=LOQ fwupd Root CA' \
    -addext 'basicConstraints=critical,CA:TRUE,pathlen:1' \
    -addext 'keyUsage=critical,keyCertSign,cRLSign' \
    -addext 'subjectKeyIdentifier=hash' \
    >/dev/null 2>&1

SIGNER_CSR="$PRIVATE_DIR/loq-community-release-signer.csr"
SIGNER_EXT="$PRIVATE_DIR/loq-community-release-signer.ext"
openssl req -newkey rsa:3072 -nodes -sha256 \
    -keyout "$PRIVATE_DIR/loq-community-release-signer.key" \
    -out "$SIGNER_CSR" \
    -subj '/O=LOQ 15AHP10 Community/CN=LOQ fwupd Release Signer' \
    >/dev/null 2>&1

printf '%s\n' \
    'basicConstraints=critical,CA:FALSE' \
    'keyUsage=critical,digitalSignature' \
    'extendedKeyUsage=codeSigning' \
    'subjectKeyIdentifier=hash' \
    'authorityKeyIdentifier=keyid,issuer' \
    > "$SIGNER_EXT"

openssl x509 -req \
    -in "$SIGNER_CSR" \
    -CA "$PUBLIC_DIR/loq-community-root-ca.pem" \
    -CAkey "$PRIVATE_DIR/loq-community-root-ca.key" \
    -CAserial "$PRIVATE_DIR/loq-community-root-ca.srl" -CAcreateserial \
    -out "$PUBLIC_DIR/loq-community-release-signer.pem" \
    -days 825 -sha256 -extfile "$SIGNER_EXT" \
    >/dev/null 2>&1

chmod 0600 "$PRIVATE_DIR/loq-community-root-ca.key" \
    "$PRIVATE_DIR/loq-community-release-signer.key" \
    "$SIGNER_CSR" "$SIGNER_EXT" \
    "$PRIVATE_DIR/loq-community-root-ca.srl"
chmod 0644 "$PUBLIC_DIR/loq-community-root-ca.pem" \
    "$PUBLIC_DIR/loq-community-release-signer.pem"

printf 'created key material under %s\n' "$KEY_ROOT"
printf 'root CA SHA-256 fingerprint: '
openssl x509 -in "$PUBLIC_DIR/loq-community-root-ca.pem" \
    -noout -fingerprint -sha256 | sed 's/^.*=//'
