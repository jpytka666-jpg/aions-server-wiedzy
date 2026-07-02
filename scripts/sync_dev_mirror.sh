#!/usr/bin/env bash
# One-way sync: /mnt/e/server wiedzy -> /mnt/d/AIONS_DEV/repo/server-wiedzy (WSL dev mirror).
set -euo pipefail

SOURCE="${AIONS_SYNC_SOURCE:-/mnt/e/server wiedzy}"
DEST="${AIONS_SYNC_DEST:-/mnt/d/AIONS_DEV/repo/server-wiedzy}"
DRY_RUN=0
MIRROR=0
INCLUDE_GIT=0

usage() {
  cat <<'EOF'
Usage: sync_dev_mirror.sh [--dry-run] [--mirror] [--include-git]

  --dry-run      Show what would be copied (rsync -n --stats)
  --mirror       Delete extra files in destination (--delete)
  --include-git  Copy .git (default: excluded)

Env overrides: AIONS_SYNC_SOURCE, AIONS_SYNC_DEST
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --mirror) MIRROR=1; shift ;;
    --include-git) INCLUDE_GIT=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ ! -d "$SOURCE" ]]; then
  echo "Source does not exist: $SOURCE" >&2
  exit 1
fi
mkdir -p "$DEST"

RSYNC_OPTS=(
  -a
  --human-readable
  --stats
  --exclude 'venv/'
  --exclude 'data/chroma/'
  --exclude 'scan_results/'
  --exclude '__pycache__/'
)
if [[ "$INCLUDE_GIT" -eq 0 ]]; then
  RSYNC_OPTS+=(--exclude '.git/')
fi
if [[ "$MIRROR" -eq 1 ]]; then
  RSYNC_OPTS+=(--delete)
fi
if [[ "$DRY_RUN" -eq 1 ]]; then
  RSYNC_OPTS+=(-n)
  echo "=== DRY-RUN: no files will be copied ==="
else
  echo "=== Syncing dev mirror (WSL) ==="
fi

echo "Source:      $SOURCE"
echo "Destination: $DEST"
echo ""

rsync "${RSYNC_OPTS[@]}" "${SOURCE}/" "${DEST}/"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo ""
  echo "Dry-run finished. See 'Number of regular files transferred' in stats above."
fi
