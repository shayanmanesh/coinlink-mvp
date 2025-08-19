#!/usr/bin/env bash
set -euo pipefail
echo "=== PRE-FLIGHT CHECK: environment readiness for parallel production implementation ==="

MISSING=0
REQUIRED_CMDS=(git gh docker kubectl node npm)
PYTHON_CMDS=(python python3)
found_python=false
for cmd in "${PYTHON_CMDS[@]}"; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "  ✓ $cmd"
    found_python=true
    break
  fi
done
if [ "$found_python" = false ]; then
  echo "  ✖ MISSING: python or python3"
  MISSING=$((MISSING+1))
fi
for cmd in "${REQUIRED_CMDS[@]}"; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "  ✖ MISSING: $cmd"
    MISSING=$((MISSING+1))
  else
    echo "  ✓ $cmd"
  fi
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "  ✖ Not inside a git repo. Run this from repo root (or initialize one)."
  MISSING=$((MISSING+1))
else
  echo "  ✓ Inside git repo"
fi

if command -v gh >/dev/null 2>&1; then
  if ! gh auth status >/dev/null 2>&1; then
    echo "  ✖ gh not authenticated. Run: gh auth login"
    MISSING=$((MISSING+1))
  else
    echo "  ✓ gh authenticated"
  fi
fi

REQUIRED_ENVS=( GITHUB_TOKEN DOCKER_REGISTRY DOCKER_USERNAME DATABASE_URL REDIS_URL )
for var in "${REQUIRED_ENVS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "  ⚠ env unset: $var  (set if you plan to integrate this service)"
  else
    echo "  ✓ $var set"
  fi
done

if [ "$MISSING" -ne 0 ]; then
  echo ""
  echo "!!! PRE-FLIGHT FAILED: $MISSING missing CLI(s). Install them and re-run preflight."
  exit 2
fi

echo "=== PRE-FLIGHT OK ==="
exit 0