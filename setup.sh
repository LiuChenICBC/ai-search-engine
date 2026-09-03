#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

GITHUB_REPO="${1:?Usage: ./setup.sh <github-repo-url>}"

echo "🚀 Setting up www_search..."

# Initialize git if not already done
if [ ! -d .git ]; then
    git init
    git branch -M main
fi

# Add remote
git remote remove origin 2>/dev/null || true
git remote add origin "$GITHUB_REPO"

# Commit any changes
git add -A
if git diff --cached --quiet; then
    echo "No changes to commit."
else
    git commit -m "update: $(date '+%Y-%m-%d')"
fi

# Push
git push -u origin main
git push --tags

echo "✅ Pushed to $GITHUB_REPO"
echo ""
echo "Next steps:"
echo "  1. Go to $GITHUB_REPO on GitHub"
echo "  2. Create a release: Settings → Releases → Draft a new release"
echo "  3. Tag: v1.0.0, Title: v1.0.0 Initial Release"