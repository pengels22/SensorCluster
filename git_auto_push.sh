#!/bin/bash

REPO_DIR="$HOME/Cluster"
WATCH_DIR="$HOME/Cluster"
EXCLUDES=".*(\.log|\.tmp|\.pyc|__pycache__).*"

cd "$REPO_DIR" || exit 1
echo "? Watching: $WATCH_DIR"

while true; do
  inotifywait -r -e modify,create,delete,move "$WATCH_DIR" --excludei "$EXCLUDES"
  echo "? Change detected. Committing and pushing..."

  git add -A
  git commit -m "Auto-push update: $(date '+%Y-%m-%d %H:%M:%S')"
  git push

  [ -f "$REPO_DIR/generate_changelog.sh" ] && bash "$REPO_DIR/generate_changelog.sh"
  echo "? Push complete"
done
