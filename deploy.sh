#!/bin/sh
# Publish HEAD to both hosts, which don't sync with each other:
#   GitHub Pages     https://ivancuric.github.io/yi-ekpilot-guide/  (serves branch main)
#   Cloudflare Pages https://yi-ekpilot.pages.dev  (project yi-ekpilot, direct upload, no Git connection)
set -eu
cd "$(dirname "$0")"
python3 build.py --check
[ -z "$(git status --porcelain)" ] || { echo 'deploy.sh: uncommitted changes; this deploys HEAD' >&2; exit 1; }
[ "$(git branch --show-current)" = main ] || { echo 'deploy.sh: not on main' >&2; exit 1; }
git push origin main
dist=$(mktemp -d); trap 'rm -rf "$dist"' EXIT
git archive HEAD | tar -x -C "$dist"   # .gitattributes keeps the tooling out
npx wrangler pages deploy "$dist" --project-name yi-ekpilot --branch main \
  --commit-hash "$(git rev-parse HEAD)" --commit-message "$(git log -1 --format=%s)"
