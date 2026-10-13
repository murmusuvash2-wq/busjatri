#!/usr/bin/env bash
# scripts/push_retry.sh - push without losing the race.
#
# Every build commits (page regen), and several workflows can finish at the same
# time. A plain `git push` then dies with "non-fast-forward". This rebases onto
# the remote and retries. It also stops tracking Python bytecode caches - those
# were being committed by `git add -A` on every run and were what made each
# build look "changed", triggering the races in the first place.
#
# Usage: bash scripts/push_retry.sh [branch]
set -uo pipefail

BRANCH="${1:-${GITHUB_REF_NAME:-main}}"

# untrack bytecode caches (no-op once done)
git rm -r --cached --ignore-unmatch --quiet scripts/__pycache__ 2>/dev/null || true
if ! git diff --staged --quiet; then
  git commit -q -m "chore: untrack __pycache__ [skip ci]" || true
fi

for i in 1 2 3 4 5; do
  git pull --rebase --autostash origin "$BRANCH" >/dev/null 2>&1 || true
  if git push origin "HEAD:$BRANCH" 2>/dev/null; then
    echo "push ok (attempt $i)"
    exit 0
  fi
  echo "push attempt $i failed - retrying in $((i*3))s"
  sleep $((i*3))
done
echo "push failed after 5 attempts"
exit 1
