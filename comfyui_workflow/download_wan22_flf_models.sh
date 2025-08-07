#!/bin/bash

# WAN2.2 FLF models download script

MODEL_DIR="/home/kazuph/runpod-wan2.2-api/comfyui_workflow/models"

echo "Downloading WAN2.2 FLF models..."

# Create directories if they don't exist
mkdir -p $MODEL_DIR/diffusion_models
mkdir -p $MODEL_DIR/text_encoders
mkdir -p $MODEL_DIR/vae

# Download high noise model (if not exists)
if [ ! -f "$MODEL_DIR/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors" ]; then
    echo "Downloading WAN2.2 high noise model..."
    wget -c https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors \
         -O $MODEL_DIR/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors
fi

# Download low noise model (if not exists)
if [ ! -f "$MODEL_DIR/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors" ]; then
    echo "Downloading WAN2.2 low noise model..."
    wget -c https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors \
         -O $MODEL_DIR/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors
fi

# Download text encoder (if not exists)
if [ ! -f "$MODEL_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" ]; then
    echo "Downloading UMT5 text encoder..."
    wget -c https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors \
         -O $MODEL_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
fi

# Download VAE (if not exists)
if [ ! -f "$MODEL_DIR/vae/wan_2.1_vae.safetensors" ]; then
    echo "Downloading WAN VAE..."
    wget -c https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors \
         -O $MODEL_DIR/vae/wan_2.1_vae.safetensors
fi

echo "Model download complete!"
ls -lh $MODEL_DIR/diffusion_models/
ls -lh $MODEL_DIR/text_encoders/
ls -lh $MODEL_DIR/vae/