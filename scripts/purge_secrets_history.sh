#!/usr/bin/env bash
# Purge leaked secrets (and .venv bloat) from git history across all branches.
# See docs/adr/ADR-007-secret-history-purge.md. DESTRUCTIVE — rewrites history.
#
# The replacements file must be created OUTSIDE the repo and must NOT be
# committed. Each line: <literal-secret>==>***REMOVED***
#
# Usage:
#   scripts/purge_secrets_history.sh /abs/path/to/replacements.txt
set -euo pipefail

REPL="${1:?Provide path to replacements.txt (outside the repo)}"
REMOTE="https://github.com/AlfonsoCifuentes/riskmap.git"

command -v git-filter-repo >/dev/null 2>&1 || {
  echo "git-filter-repo not found. Install: pip install git-filter-repo"; exit 1; }

echo ">> Rewriting history: redacting secrets + dropping .venv ..."
git filter-repo --replace-text "$REPL" --path .venv --invert-paths --force

echo ">> Re-adding origin (filter-repo removes it as a safety measure) ..."
git remote remove origin 2>/dev/null || true
git remote add origin "$REMOTE"

echo ">> Force-pushing rewritten refs ..."
git push --force --all
git push --force --tags

echo ">> Done. Delete the replacements file now: rm '$REPL'"
echo ">> REMINDER: history purge != key revocation. Rotate the keys."
