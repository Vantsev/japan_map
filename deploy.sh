#!/usr/bin/env bash
# Keikenchi — deploy to Cloudflare Pages + D1.
# Run interactively:  ./deploy.sh   (wrangler needs a browser login the first time)
set -euo pipefail
cd "$(dirname "$0")"

echo "▶ 1/5 build front"
python3 build.py

echo "▶ 2/5 wrangler login (skip if already logged in)"
npx --yes wrangler whoami >/dev/null 2>&1 || npx --yes wrangler login

echo "▶ 3/5 D1 database"
if grep -q REPLACE_WITH_D1_ID wrangler.toml; then
  OUT=$(npx --yes wrangler d1 create keikenchi || true)
  echo "$OUT"
  ID=$(printf '%s' "$OUT" | grep -oE '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' | head -1)
  if [ -n "${ID:-}" ]; then
    sed -i '' "s/REPLACE_WITH_D1_ID/$ID/" wrangler.toml
    echo "  wrote database_id=$ID into wrangler.toml"
  else
    echo "  ! could not auto-detect database_id — paste it into wrangler.toml manually, then re-run"; exit 1
  fi
else
  echo "  database_id already set, skipping create"
fi

echo "▶ 4/5 apply schema (remote)"
npx --yes wrangler d1 execute keikenchi --remote --file schema.sql

echo "▶ 5/5 deploy Pages"
npx --yes wrangler pages deploy public --project-name keikenchi

echo "✅ done — open the *.pages.dev URL above"
