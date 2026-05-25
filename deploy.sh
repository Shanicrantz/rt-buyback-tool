#!/usr/bin/env bash
# ============================================================
# RT Buyback Tool — Netlify deploy script
# Run this from Claude Code (terminal) inside the cc-package folder.
# ============================================================
set -e

SITE_ID="7b706fe7-9260-4d82-a0ff-263413316382"

echo "==> RT Buyback Tool deploy to Netlify"
echo "    Site: rt-buyback-tool ($SITE_ID)"
echo ""

# 1. Ensure Netlify CLI present
if ! command -v netlify >/dev/null 2>&1; then
  echo "==> Installing netlify-cli..."
  npm install -g netlify-cli
fi

# 2. Ensure logged in
if ! netlify status >/dev/null 2>&1; then
  echo "==> Not logged in. Opening Netlify login..."
  netlify login
fi

# 3. Build a clean dist folder (only index.html)
echo "==> Preparing clean dist/ (index.html only)"
rm -rf dist
mkdir -p dist
cp index.html dist/index.html

# 4. Deploy to production
echo "==> Deploying to production..."
netlify deploy --site="$SITE_ID" --dir=dist --prod

echo ""
echo "==> Done. Live at https://rt-buyback-tool.netlify.app"
echo "    Password: rajdhani2026"
