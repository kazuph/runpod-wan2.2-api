#!/usr/bin/env bash

# Start script for FLF service
# Based on Flux ComfyUI architecture

set -e

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Set environment variables
export PYTHONUNBUFFERED=1
export CUDA_VISIBLE_DEVICES=0

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "Running in Docker container"
    COMFYUI_PATH="/comfyui"
else
    echo "Running on host system"
    COMFYUI_PATH="/home/kazuph/runpod-wan2.2-api/comfyui_workflow/comfyui_workflow"
fi

# Start ComfyUI in background
echo "Starting ComfyUI server..."
cd $COMFYUI_PATH
python main.py --disable-auto-launch --listen --port 8188 &
COMFYUI_PID=$!
echo "ComfyUI PID: $COMFYUI_PID"

# Wait for ComfyUI to be ready
echo "Waiting for ComfyUI to be ready..."
for i in {1..60}; do
    if curl -s http://127.0.0.1:8188/system_stats > /dev/null; then
        echo "ComfyUI is ready!"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "ComfyUI failed to start"
        exit 1
    fi
    sleep 1
done

# Check if we should serve API locally
if [ "$SERVE_API_LOCALLY" == "true" ] || [ "$1" == "--serve-api" ]; then
    echo "Starting RunPod API server locally on port 8080..."
    cd /home/kazuph/runpod-wan2.2-api/flf
    python3 -u rp_handler.py --rp_serve_api --rp_api_host=0.0.0.0 --rp_api_port=8080
else
    echo "Starting RunPod handler..."
    cd /home/kazuph/runpod-wan2.2-api/flf
    python3 -u rp_handler.py
fi

# Cleanup on exit
trap "kill $COMFYUI_PID 2>/dev/null" EXIT