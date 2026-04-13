#!/bin/bash

# Versiyon dosyasını oku
VERSION_FILE=".version"
VERSION=$(cat "$VERSION_FILE" | tr -d '\n')

# Versiyon numarasını artır (1.4.4 -> 1.4.5)
IFS='.' read -r major minor patch <<< "$VERSION"
patch=$((patch + 1))
NEW_VERSION="$major.$minor.$patch"

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
