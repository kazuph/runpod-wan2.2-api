#!/bin/bash

# Remove broken symlink if exists
rm -f /content/ComfyUI/models/diffusion_models/Wan2.1-FLF2V-14B-720P

# Copy model from checkpoints to diffusion_models for proper loading
if [ -d "/content/ComfyUI/models/checkpoints/Wan2.1-FLF2V-14B-720P" ]; then
    echo "Copying FLF model to diffusion_models directory..."
    cp -r /content/ComfyUI/models/checkpoints/Wan2.1-FLF2V-14B-720P /content/ComfyUI/models/diffusion_models/
    echo "Model copy completed."
fi

# Start the application
python "$@"