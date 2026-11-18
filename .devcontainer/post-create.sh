#!/bin/bash
set -euo pipefail

if [ ! -f agent/config/.env.local ] && [ -f agent/config/.env.example ]; then
  cp agent/config/.env.example agent/config/.env.local
fi

if [ ! -f copilot/.env.local ] && [ -f copilot/.env.local.example ]; then
  cp copilot/.env.local.example copilot/.env.local
fi

corepack enable
corepack prepare yarn@1.22.22 --activate
yarn install --frozen-lockfile

if command -v curl >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

export PATH="${HOME}/.local/bin:${PATH}"
(cd agent && uv sync)
