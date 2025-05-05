#!/bin/bash

# This script generates all the required icon formats for The Engineer app
# Requirements: ImageMagick (convert, identify commands)

# Check if source icon exists
if [ ! -f "icon_source.png" ]; then
    echo "Error: Source icon 'icon_source.png' not found."
    echo "Please provide a source PNG image (at least 1024x1024 pixels) named 'icon_source.png'"
    exit 1
fi

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null || ! command -v identify &> /dev/null; then
    echo "Error: ImageMagick is not installed or not in PATH"
    echo "Please install ImageMagick to continue"
    exit 1
fi

# Check source icon size
size=$(identify -format "%wx%h" icon_source.png)
width=$(identify -format "%w" icon_source.png)
height=$(identify -format "%h" icon_source.png)

if [ $width -lt 1024 ] || [ $height -lt 1024 ]; then
    echo "Warning: Source icon is smaller than recommended ($size)."
    echo "For best results, please use an image at least 1024x1024 pixels."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Generating icons from source icon ($size)..."

# Generate Windows ICO file
echo "Generating Windows .ico file..."
convert icon_source.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico

# Generate macOS ICNS file (requires intermediate .iconset directory)
echo "Generating macOS .icns file..."
mkdir -p icon.iconset
convert icon_source.png -resize 16x16 icon.iconset/icon_16x16.png
convert icon_source.png -resize 32x32 icon.iconset/icon_16x16@2x.png
convert icon_source.png -resize 32x32 icon.iconset/icon_32x32.png
convert icon_source.png -resize 64x64 icon.iconset/icon_32x32@2x.png
convert icon_source.png -resize 128x128 icon.iconset/icon_128x128.png
convert icon_source.png -resize 256x256 icon.iconset/icon_128x128@2x.png
convert icon_source.png -resize 256x256 icon.iconset/icon_256x256.png
convert icon_source.png -resize 512x512 icon.iconset/icon_256x256@2x.png
convert icon_source.png -resize 512x512 icon.iconset/icon_512x512.png
convert icon_source.png -resize 1024x1024 icon.iconset/icon_512x512@2x.png

# If we're on macOS, use iconutil to create the .icns file
if [[ "$OSTYPE" == "darwin"* ]]; then
    iconutil -c icns icon.iconset
    rm -rf icon.iconset
else
    echo "Not on macOS - .iconset directory created, but .icns file needs to be generated on a Mac"
    echo "Convert using: iconutil -c icns icon.iconset"
fi

# Generate Linux/Standard PNG icons in various sizes
echo "Generating PNG icons in multiple sizes..."
convert icon_source.png -resize 16x16 icon-16x16.png
convert icon_source.png -resize 32x32 icon-32x32.png
convert icon_source.png -resize 48x48 icon-48x48.png
convert icon_source.png -resize 64x64 icon-64x64.png
convert icon_source.png -resize 128x128 icon-128x128.png
convert icon_source.png -resize 256x256 icon-256x256.png
convert icon_source.png -resize 512x512 icon-512x512.png
convert icon_source.png -resize 1024x1024 icon-1024x1024.png

# Copy the main app icon
cp icon-512x512.png icon.png

echo "Icon generation complete!"
echo "Generated files:"
echo "- icon.ico (Windows)"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "- icon.icns (macOS)"
else
    echo "- icon.iconset/ (for macOS .icns generation)"
fi
echo "- icon-*.png (Multiple PNG sizes for various platforms)"
echo "- icon.png (Main app icon at 512x512)"