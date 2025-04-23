#!/bin/bash

# === Configuration ===
VERSION_FILE="VERSION"
CHANGELOG_FILE="CHANGELOG.md"

# === Ensure required files exist ===
if [ ! -f "$VERSION_FILE" ]; then
  echo "v1.2.0" > "$VERSION_FILE"
  echo "📄 Created VERSION file with default version v1.2.0"
fi

if [ ! -f "$CHANGELOG_FILE" ]; then
  echo "# Changelog" > "$CHANGELOG_FILE"
  echo "" >> "$CHANGELOG_FILE"
  echo "📄 Created CHANGELOG.md"
fi

# === Get last version ===
LAST_VERSION=$(cat "$VERSION_FILE")
IFS='.' read -r major minor patch <<< "${LAST_VERSION//v/}"

# === Bump patch version ===
patch=$((patch + 1))
NEW_VERSION="v$major.$minor.$patch"

# === Append to CHANGELOG.md ===
echo "## $NEW_VERSION - $(date '+%Y-%m-%d %H:%M:%S')" >> "$CHANGELOG_FILE"
git log "$LAST_VERSION"..HEAD --pretty=format:"- %s" >> "$CHANGELOG_FILE"
echo -e "\n" >> "$CHANGELOG_FILE"

# === Update VERSION file ===
echo "$NEW_VERSION" > "$VERSION_FILE"

# === Git commit + tag + push ===
git add "$VERSION_FILE" "$CHANGELOG_FILE"
git commit -m "Version bump to $NEW_VERSION"
git tag "$NEW_VERSION"
git push
git push origin "$NEW_VERSION"

echo "✅ Changelog updated and tagged as $NEW_VERSION"
