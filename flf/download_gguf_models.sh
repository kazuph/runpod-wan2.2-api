#!/bin/bash

# Download WAN2.1 FLF GGUF models for 24GB VRAM
# Using Q6_K quantization for best quality/performance balance

set -e

MODEL_DIR="./models"
mkdir -p "$MODEL_DIR/unet_gguf" "$MODEL_DIR/clip" "$MODEL_DIR/vae"

echo "🚀 Downloading WAN2.1 FLF GGUF Models (Q6_K - 14.2GB)"
echo "================================================"

# Download GGUF model (Q6_K for best balance)
MODEL_NAME="Wan2.1-FLF2V-14B-720P-Q6_K.gguf"
MODEL_URL="https://huggingface.co/city96/Wan2.1-FLF2V-14B-720P-gguf/resolve/main/${MODEL_NAME}"

if [ ! -f "$MODEL_DIR/unet_gguf/${MODEL_NAME}" ]; then
    echo "📥 Downloading ${MODEL_NAME} (14.2 GB)..."
    wget -q --show-progress -O "$MODEL_DIR/unet_gguf/${MODEL_NAME}" "${MODEL_URL}"
    echo "✅ Downloaded ${MODEL_NAME}"
else
    echo "✓ ${MODEL_NAME} already exists"
fi

# Download T5 XXL text encoder (FP8 for memory efficiency)
T5_MODEL="t5xxl_fp8_e4m3fn.safetensors"
T5_URL="https://huggingface.co/Comfy-Org/mochi_preview_repackaged/resolve/main/text_encoders/t5xxl_fp8_e4m3fn.safetensors"

if [ ! -f "$MODEL_DIR/clip/${T5_MODEL}" ]; then
    echo "📥 Downloading T5 XXL text encoder (FP8)..."
    wget -q --show-progress -O "$MODEL_DIR/clip/${T5_MODEL}" "${T5_URL}"
    echo "✅ Downloaded ${T5_MODEL}"
else
    echo "✓ T5 XXL encoder already exists"
fi

# Download CLIP L encoder
CLIP_MODEL="clip_l.safetensors"
CLIP_URL="https://huggingface.co/Comfy-Org/mochi_preview_repackaged/resolve/main/text_encoders/clip_l.safetensors"

if [ ! -f "$MODEL_DIR/clip/${CLIP_MODEL}" ]; then
    echo "📥 Downloading CLIP L encoder..."
    wget -q --show-progress -O "$MODEL_DIR/clip/${CLIP_MODEL}" "${CLIP_URL}"
    echo "✅ Downloaded ${CLIP_MODEL}"
else
    echo "✓ CLIP L encoder already exists"
fi

# Download WAN2.1 VAE
VAE_MODEL="Wan2.1_VAE.pth"
VAE_URL="https://huggingface.co/Wan-AI/Wan2.1-FLF2V-14B-720P/resolve/main/Wan2.1_VAE.pth"

if [ ! -f "$MODEL_DIR/vae/${VAE_MODEL}" ]; then
    echo "📥 Downloading WAN2.1 VAE..."
    wget -q --show-progress -O "$MODEL_DIR/vae/${VAE_MODEL}" "${VAE_URL}"
    echo "✅ Downloaded ${VAE_MODEL}"
else
    echo "✓ WAN2.1 VAE already exists"
fi

# Alternative quantizations available (uncomment to download)
echo ""
echo "📊 Alternative GGUF Quantizations Available:"
echo "  Q8_0 (18.1 GB) - Highest quality"
echo "  Q6_K (14.2 GB) - Best balance ✅ [Downloaded]"
echo "  Q5_K_M (12.7 GB) - Good balance"
echo "  Q4_K_M (11.3 GB) - Fast inference"
echo "  Q3_K_M (8.59 GB) - Fastest, lower quality"
echo ""
echo "To download other versions, modify MODEL_NAME in this script."

echo ""
echo "================================================"
echo "✅ Model setup complete!"
echo ""
echo "📁 Directory structure:"
tree -L 2 "$MODEL_DIR" 2>/dev/null || ls -la "$MODEL_DIR"/*

echo ""
echo "🎯 Next steps:"
echo "  1. Install ComfyUI-GGUF custom node"
echo "  2. Update workflow to use GGUF model"
echo "  3. Test FLF generation"