#!/usr/bin/env bash
set -euo pipefail

echo "=== BOOTSTRAP: Setting up parallel development worktrees ==="

# Ensure we're on main branch
git checkout main 2>/dev/null || git checkout -b main
git pull --rebase origin main || true

# Create baseline branch for production-ready state  
git checkout -b production-ready 2>/dev/null || git checkout production-ready

# Create worktrees home
mkdir -p .worktrees

# Define lanes for parallel development
LANES=( "fe_frontend" "be_backend" "rnd_research" "bd_business_dev" "mkt_marketing" "ops_observability" )

echo "Creating development lanes..."
for lane in "${LANES[@]}"; do
  branch="feat/${lane}"
  dir=".worktrees/${lane}"
  
  echo "  Setting up lane: $lane"
  
  # Create branch if it doesn't exist
  if ! git show-ref --verify --quiet refs/heads/"$branch"; then
    git branch "$branch" main
    echo "    ✓ Created branch: $branch"
  else
    echo "    ✓ Branch exists: $branch"
  fi
  
  # Create worktree if it doesn't exist
  if [ ! -d "$dir" ]; then
    git worktree add "$dir" "$branch"
    echo "    ✓ Created worktree: $dir"
  else
    echo "    ✓ Worktree exists: $dir"
  fi
done

echo ""
echo "=== Worktree Summary ==="
git worktree list
echo ""
echo "=== BOOTSTRAP COMPLETE ==="