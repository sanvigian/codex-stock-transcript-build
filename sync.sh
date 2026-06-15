#!/usr/bin/env bash
# ./sync.sh "message"  — stage, secret-scan, commit, and push this app to GitHub.
# Keeps local and GitHub in sync. Aborts if it detects a secret/token.
set -uo pipefail
cd "$(dirname "$0")" || exit 1
msg="${*:-update $(date +%Y-%m-%d_%H:%M)}"
git rev-parse --git-dir >/dev/null 2>&1 || { echo "Not a git repo."; exit 1; }
git remote get-url origin >/dev/null 2>&1 || { echo "No origin remote — not pushing."; exit 1; }
git add -A
if git diff --cached | grep -qE "ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16}|ya29\.[A-Za-z0-9_-]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[baprs]-[0-9A-Za-z-]{12,}"; then
  echo "⛔ ABORT: a secret/token pattern is in your staged changes. Nothing committed."
  echo "   Remove it, add it to .gitignore, then re-run."
  git reset -q; exit 1
fi
if git diff --cached --quiet; then echo "Nothing new to commit."; else git commit -q -m "$msg" && echo "✓ committed: $msg"; fi
git push -q && echo "✓ pushed to GitHub" || { echo "⛔ push failed"; exit 1; }
git status -sb | head -1
