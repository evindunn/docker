#!/bin/bash

set -e
set -o pipefail

if [ -z "$APPROLE_ID" ]; then
    echo APPROLE_ID not set
    exit 1
fi

echo "$APPROLE_ID" > /data/approle-id.txt
chmod 600 /data/approle-id.txt

gomplate -f /vault-agent.tmpl | tee /data/config.hcl

exec "$@"
