#!/bin/bash

WATCH_DIR="$HOME/Desktop/Sensor_Cluster/Cluster"
LOGFILE="$WATCH_DIR/git_watchdog.log"

cd "$WATCH_DIR" || exit 1
echo "$(date) - Starting Git Watchdog (fswatch)" >> "$LOGFILE"

fswatch -0 -r "$WATCH_DIR" | while read -d "" event
do
  echo "$(date) - Change detected: $event" >> "$LOGFILE"

  # Clean up stale lock if needed
  [ -f .git/index.lock ] && rm .git/index.lock

  # Stage, commit, and push
  git add -A
  git commit -m "Auto-push: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOGFILE" 2>&1
  git push origin main >> "$LOGFILE" 2>&1
done

