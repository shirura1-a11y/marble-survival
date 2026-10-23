#!/usr/bin/env bash
set -euo pipefail
video="${1:-output/marble_survival_001.mp4}"
test -f "$video"
gh auth status
gh auth setup-git
owner="$(gh api user --jq .login)"
repo="$owner/marble-survival"
if ! gh repo view "$repo" >/dev/null 2>&1; then
  gh repo create "$repo" --public --description 'Configurable 3D marble survival video series'
fi
if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "https://github.com/$repo.git"
fi
# If an existing remote has history, do not overwrite it or force-push.
branch="main"
if git ls-remote --exit-code origin HEAD >/dev/null 2>&1; then
  branch="$(gh repo view "$repo" --json defaultBranchRef --jq .defaultBranchRef.name)"
  git fetch origin "$branch"
  git merge FETCH_HEAD --allow-unrelated-histories --no-edit
fi
git push -u origin "HEAD:$branch"
tag="episode-001"
if ! gh release view "$tag" --repo "$repo" >/dev/null 2>&1; then
  gh release create "$tag" --repo "$repo" --target "$branch" --title 'MARBLE SURVIVAL 001' --notes '60 seconds · 1080×1920 · 30 fps · original sound effects · no narration or captions'
fi
gh release upload "$tag" "$video" --repo "$repo" --clobber
printf 'https://github.com/%s/releases/download/%s/marble_survival_001.mp4\n' "$repo" "$tag"
