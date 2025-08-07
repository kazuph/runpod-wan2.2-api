#!/bin/bash

# Install ComfyUI-VideoHelperSuite for direct video output

set -e

echo "🎥 Installing ComfyUI-VideoHelperSuite..."

CUSTOM_NODES_DIR="/home/kazuph/runpod-wan2.2-api/comfyui_workflow/custom_nodes"
mkdir -p "$CUSTOM_NODES_DIR"

cd "$CUSTOM_NODES_DIR"

# Clone VHS if not exists
if [ ! -d "ComfyUI-VideoHelperSuite" ]; then
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite
    echo "✅ VHS cloned"
else
    echo "VHS already exists, updating..."
    cd ComfyUI-VideoHelperSuite
    git pull
    cd ..
fi

# Install requirements
if [ -f "ComfyUI-VideoHelperSuite/requirements.txt" ]; then
    pip install -r ComfyUI-VideoHelperSuite/requirements.txt
    echo "✅ VHS requirements installed"
fi

echo ""
echo "✅ VideoHelperSuite installation complete!"
echo ""
echo "The following nodes are now available:"
echo "  - VHS_VideoCombine: Combine images into video directly"
echo "  - VHS_LoadVideo: Load video files"
echo "  - VHS_SplitVideo: Split video into frames"
echo ""
echo "⚠️  Note: ComfyUI needs to be restarted to load the new nodes"