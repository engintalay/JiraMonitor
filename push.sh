#!/bin/bash

# Versiyon dosyasını oku
VERSION_FILE=".version"
VERSION=$(cat "$VERSION_FILE")

# Versiyon numarasını artır (1.0.3 -> 1.0.4)
IFS='.' read -r major minor patch <<< "$VERSION"
minor=$((minor + 1))
TIMESTAMP=$(date +"%Y%m%d%H%M")
NEW_VERSION="$major.$minor.$patch.$TIMESTAMP"

# Versiyon dosyasını güncelle
echo "$NEW_VERSION" > "$VERSION_FILE"

# monitor.py'de versiyon güncelle
sed -i "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" monitor.py

# Git'e ekle ve commit yap
git add .version monitor.py
git commit -m "Version bump: $NEW_VERSION"

# Push yap
git push

echo "✅ Versiyon $NEW_VERSION olarak güncellendi ve push yapıldı."
