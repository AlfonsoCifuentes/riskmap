# ADR-007 — Purge leaked secrets from git history

- **Status:** Accepted (executed 2026-08-18)
- **Context:** The audit addendum (finding B2) discovered that `.env.example`
  was committed to this **public** repository containing real-format API keys
  (OpenAI, Groq, DeepSeek, HuggingFace, DeepL, Sentinel Hub secret, EIA), present
  since the initial commit. Sanitizing the current file is not enough — the
  values remain retrievable from history.

## Decision

1. Replace all secret values in `.env.example` with empty placeholders (done in
   the same change set as this ADR).
2. Add `gitleaks` to CI and to pre-commit so a secret can never be committed
   again.
3. Rewrite git history across **all** branches with `git filter-repo
   --replace-text`, redacting each leaked value to `***REMOVED***`, and (in the
   same pass) drop the tracked `.venv/` virtualenv and large binary blobs to
   shrink the repository. Force-push all refs.

The exact secret strings are **not** recorded in this repo. They live only in the
operator's local `replacements.txt` used by the purge and are deleted afterward.

## Consequence & honest limitation

History rewriting changes every commit hash; any existing clone/fork must be
re-cloned. **Crucially, purging history is not the same as revoking a key.**
Anyone who cloned the repo, or any cached view (GitHub commit cache, forks,
third-party mirrors), may still hold the exposed values.

> **Recommendation to the owner:** rotate/revoke every exposed key at its
> provider. The owner has chosen not to rotate at this time; this ADR records
> that decision and its residual risk. Until rotation, treat the keys as
> compromised.

## Runbook

See `scripts/purge_secrets_history.sh`. Summary:

```bash
pip install git-filter-repo
# Create replacements.txt OUTSIDE the repo (one 'SECRET==>***REMOVED***' per line)
git filter-repo --replace-text /path/to/replacements.txt \
                --path .venv --invert-paths --force
git remote add origin https://github.com/AlfonsoCifuentes/riskmap.git
git push --force --all && git push --force --tags
rm /path/to/replacements.txt
```
