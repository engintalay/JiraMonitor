#!/bin/bash

# Versiyon dosyasını oku
VERSION_FILE=".version"
VERSION=$(cat "$VERSION_FILE")

# Versiyon numarasını artır - son part'ı alıp artır
IFS='.' read -ra PARTS <<< "$VERSION"
LAST_PART="${PARTS[-1]}"
# Sayısal kısım
NUM_PART=$(echo "$LAST_PART" | grep -oE '^[0-9]+')
if [ -z "$NUM_PART" ]; then
    NUM_PART=1
else
    NUM_PART=$((NUM_PART + 1))
fi
TIMESTAMP=$(date +"%Y%m%d%H%M")
NEW_VERSION="1.0.3.$TIMESTAMP$NUM_PART"

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
