#!/bin/sh
set -e

CERT_DIR=/etc/nginx/certs

if [ -f "$CERT_DIR/tls.crt" ] && [ -f "$CERT_DIR/tls.key" ]; then
    echo "05-generate-cert: certyfikat już istnieje, pomijam generowanie"
    exit 0
fi

echo "05-generate-cert: generuję certyfikat dla ${SERVER_NAME}"
mkdir -p "$CERT_DIR"

openssl req -x509 -noenc -newkey rsa:2048 -days 3650 \
    -keyout "$CERT_DIR/tls.key" \
    -out "$CERT_DIR/tls.crt" \
    -subj "/CN=${SERVER_NAME}" \
    -addext "subjectAltName=DNS:${SERVER_NAME},DNS:localhost,IP:127.0.0.1"