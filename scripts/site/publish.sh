#!/usr/bin/env bash
# Copy the guided tour website (docs/) into a checkout of the simple-meridian-demo repository.
#
#   scripts/site/publish.sh [path-to-demo-checkout]     # default: ../simple-meridian-demo
#
# Stamps the site's file links first, so browsers load the new files right after a publish.
# It does not commit or push: review the diff in the demo checkout, then commit and push there.
set -euo pipefail
cd "$(dirname "$0")/../.."
DEST="${1:-../simple-meridian-demo}"

if [ ! -d "$DEST/.git" ]; then
  echo "No git checkout at $DEST. Clone https://github.com/alibb007/simple-meridian-demo there first."
  exit 1
fi

python3 scripts/site/stamp_assets.py
rsync -a --delete --exclude .git --exclude README.md --exclude .gitignore --exclude __pycache__ docs/ "$DEST/"
echo "Copied docs/ to $DEST"
git -C "$DEST" status --short
