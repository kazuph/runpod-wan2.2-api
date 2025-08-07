#!/bin/bash

# Install ComfyUI-GGUF custom node for GGUF model support

set -e

echo "🔧 Installing ComfyUI-GGUF custom node..."

# Create custom_nodes directory if it doesn't exist
CUSTOM_NODES_DIR="/home/kazuph/runpod-wan2.2-api/comfyui_workflow/custom_nodes"
mkdir -p "$CUSTOM_NODES_DIR"

# Clone ComfyUI-GGUF
cd "$CUSTOM_NODES_DIR"
if [ ! -d "ComfyUI-GGUF" ]; then
    git clone https://github.com/city96/ComfyUI-GGUF
    echo "✅ ComfyUI-GGUF cloned"
else
    echo "✓ ComfyUI-GGUF already exists, updating..."
    cd ComfyUI-GGUF
    git pull
    cd ..
fi

# Install requirements if they exist
if [ -f "ComfyUI-GGUF/requirements.txt" ]; then
    pip install -r ComfyUI-GGUF/requirements.txt
    echo "✅ Requirements installed"
fi

# Check if gguf library is installed
pip show gguf > /dev/null 2>&1 || pip install gguf

echo ""
echo "✅ ComfyUI-GGUF installation complete!"
echo ""
echo "The following GGUF nodes are now available:"
echo "  - UnetLoaderGGUF: Load GGUF quantized models"
echo "  - DualCLIPLoaderGGUF: Load GGUF CLIP models"
echo ""
echo "Place GGUF models in: models/unet_gguf/"