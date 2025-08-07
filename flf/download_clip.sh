#!/bin/bash
# Download CLIP model for FLF
cd /home/kazuph/runpod-wan2.2-api/flf/models/clip
wget -q https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/t5xxl_fp8_e4m3fn.safetensors -O umt5_xxl_fp8_e4m3fn_scaled.safetensors
echo "✅ CLIP model downloaded"