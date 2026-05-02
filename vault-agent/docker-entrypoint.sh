#!/bin/bash

set -e
set -o pipefail

if [ -z "$VAULT_ADDR" ]; then
    echo VAULT_ADDR not set
    exit 1
fi

if [ -z "$CERT_PKI_ROLE" ]; then
    echo CERT_PKI_ROLE not set
    exit 1
fi

if [ -z "$CERT_COMMON_NAME" ]; then
    echo CERT_COMMON_NAME not set
    exit 1
fi

if [ -z "$CERT_APPROLE_ID" ]; then
    echo CERT_APPROLE_ID not set
    exit 1
fi

echo "$CERT_APPROLE_ID" > /data/.approle-id

gomplate --left-delim '<%' --right-delim '%>' -f vault-agent.ctmpl | tee /data/vault-agent.hcl

exec "$@"
