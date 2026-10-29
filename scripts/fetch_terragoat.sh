#!/usr/bin/env bash
# Fetch TerraGoat at pinned commit hash
set -euo pipefail

PINNED_COMMIT="729f8da62c6a85ce4af5ad3d123de97776d954c4"
TARGET_DIR="${1:-data/terragoat}"

echo "Fetching TerraGoat repository at pinned commit: ${PINNED_COMMIT}..."

if [ -d "${TARGET_DIR}/.git" ]; then
    echo "Directory ${TARGET_DIR} already exists. Verifying commit..."
    cd "${TARGET_DIR}"
    git fetch --all --tags
    git checkout -q "${PINNED_COMMIT}"
    echo "Checked out pinned commit: $(git rev-parse HEAD)"
else
    mkdir -p "$(dirname "${TARGET_DIR}")"
    git clone https://github.com/bridgecrewio/terragoat.git "${TARGET_DIR}"
    cd "${TARGET_DIR}"
    git checkout -q "${PINNED_COMMIT}"
    echo "Cloned and checked out pinned commit: $(git rev-parse HEAD)"
fi

echo "TerraGoat AWS path: ${TARGET_DIR}/terraform/aws"
