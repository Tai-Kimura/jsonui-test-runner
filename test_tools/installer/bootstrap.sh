#!/usr/bin/env bash
#
# COMPATIBILITY REDIRECT
#
# The jsonui-test CLI moved from jsonui-test-runner to the jsonui-cli monorepo
# (test_tools/). This script is kept only so old install commands keep working;
# it forwards to the canonical installer hosted in jsonui-cli. All arguments
# (-v/--version, -d/--directory, --dev, ...) are passed through unchanged.
#
# Canonical command going forward:
#   curl -fsSL https://raw.githubusercontent.com/Tai-Kimura/jsonui-cli/main/test_tools/installer/bootstrap.sh | bash

set -e

CANONICAL_URL="https://raw.githubusercontent.com/Tai-Kimura/jsonui-cli/main/test_tools/installer/bootstrap.sh"

echo "note: the jsonui-test CLI now lives in jsonui-cli — forwarding to $CANONICAL_URL" >&2

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
if ! curl -fsSL "$CANONICAL_URL" -o "$TMP" || [ ! -s "$TMP" ]; then
    echo "error: could not download the canonical jsonui-cli installer ($CANONICAL_URL)" >&2
    exit 1
fi
bash "$TMP" "$@"
