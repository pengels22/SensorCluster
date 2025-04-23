#!/bin/bash

# === Config ===
REPO_DIR="/home/pi/Cluster"
WATCH_DIRS=("/home/pi/Cluster")
EXCLUDES=".*(\\.log|\\.tmp|\\.pyc|__pycache__).*"

cd "$REPO_DIR" || exit 1

echo "? Watching folder: $REPO_DIR"
echo "? Waiting for file changes..."

while true; do
  inotifywait -r -e modify,create,delete,move "${WATCH_DIRS[@]}" --excludei "$EXCLUDES"
  echo "?? Change detected. Committing and pushing..."

  git add .
  git commit -m "Auto-push update: $(date '+%Y-%m-%d %H:%M:%S')"
  git push

  # Optional: If generate_changelog.sh lives here, run it
  if [ -f "$REPO_DIR/generate_changelog.sh" ]; then
    bash "$REPO_DIR/generate_changelog.sh"
  fi

  echo "? Push complete with version update"
done
