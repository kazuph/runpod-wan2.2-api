#!/bin/bash

# Script to download WAN2.2 FLF models
# Based on research and available models

set -e

MODEL_DIR="./models"
mkdir -p "$MODEL_DIR/unet" "$MODEL_DIR/clip" "$MODEL_DIR/vae" "$MODEL_DIR/checkpoints"

echo "📥 Downloading WAN2.2 FLF models..."
echo "This may take a while depending on your internet connection."
echo "================================================"

# Download VAE
if [ ! -f "$MODEL_DIR/vae/wan2.2_vae.safetensors" ]; then
    echo "Downloading WAN2.2 VAE..."
    wget -q --show-progress -O "$MODEL_DIR/vae/wan2.2_vae.safetensors" \
        "https://huggingface.co/camenduru/wan/resolve/main/wan2.2_vae.safetensors"
else
    echo "✓ VAE already exists"
fi

# Download CLIP text encoder (T5-XXL)
if [ ! -f "$MODEL_DIR/clip/umt5_xxl_fp8_e4m3fn_scaled.safetensors" ]; then
    echo "Downloading UMT5-XXL text encoder..."
    wget -q --show-progress -O "$MODEL_DIR/clip/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
        "https://huggingface.co/Comfy-Org/mochi_preview_repackaged/resolve/main/text_encoders/t5xxl_scaled_fp8_e4m3fn.safetensors"
else
    echo "✓ Text encoder already exists"
fi

# Try to find WAN2.2 FLF models
echo ""
echo "⚠️  Note: WAN2.2 FLF-specific models need to be obtained separately."
echo "The following models are required for FLF:"
echo "  - wan2.2-flf-high.safetensors (HIGH noise model)"
echo "  - wan2.2-flf-low.safetensors (LOW noise model)"
echo ""
echo "Attempting to use WAN2.2 I2V models as fallback..."

# Try to use existing I2V models as fallback for FLF
# Check if WAN2.2 I2V models exist in the parent directory
PARENT_MODEL_DIR="../rapid-i2v/models"
COMFYUI_MODEL_DIR="../comfyui_workflow/models"

if [ -f "$COMFYUI_MODEL_DIR/diffusion_models/wan2.2-i2v-rapid.safetensors" ]; then
    echo "Found WAN2.2 I2V model in ComfyUI directory, creating symlinks..."
    ln -sf "../../comfyui_workflow/models/diffusion_models/wan2.2-i2v-rapid.safetensors" \
        "$MODEL_DIR/unet/wan2.2-flf-high.safetensors"
    ln -sf "../../comfyui_workflow/models/diffusion_models/wan2.2-i2v-rapid.safetensors" \
        "$MODEL_DIR/unet/wan2.2-flf-low.safetensors"
    echo "✓ Created symlinks to I2V model for FLF testing"
elif [ -f "$PARENT_MODEL_DIR/diffusion_models/wan2.2-i2v-rapid.safetensors" ]; then
    echo "Found WAN2.2 I2V model in rapid-i2v directory, creating symlinks..."
    ln -sf "../../rapid-i2v/models/diffusion_models/wan2.2-i2v-rapid.safetensors" \
        "$MODEL_DIR/unet/wan2.2-flf-high.safetensors"
    ln -sf "../../rapid-i2v/models/diffusion_models/wan2.2-i2v-rapid.safetensors" \
        "$MODEL_DIR/unet/wan2.2-flf-low.safetensors"
    echo "✓ Created symlinks to I2V model for FLF testing"
else
    echo ""
    echo "❌ WAN2.2 models not found. Please download them manually:"
    echo "   1. Download WAN2.2 FLF models from HuggingFace or other sources"
    echo "   2. Place them in $MODEL_DIR/unet/"
    echo "   3. Name them: wan2.2-flf-high.safetensors and wan2.2-flf-low.safetensors"
fi

echo ""
echo "================================================"
echo "Model setup complete!"
echo ""
echo "Directory structure:"
tree -L 2 "$MODEL_DIR" 2>/dev/null || ls -la "$MODEL_DIR"/*