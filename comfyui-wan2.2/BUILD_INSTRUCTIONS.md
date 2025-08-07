# ComfyUI WAN2.2 GGUF Docker Build Instructions

This repository contains Dockerfiles reverse-engineered from `nykk3/comfyui-wan2.2-gguf:q4ks-14b-i2v-cuda12.8`.

## Files Overview

- `Dockerfile` - Simple single-stage build
- `Dockerfile.optimized` - Multi-stage optimized build with better caching
- `docker-compose.yml` - Docker Compose configuration with GPU support

## Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# Build and run with model downloads (takes ~1-2 hours)
docker compose up -d comfyui-wan22-gguf

# Or build slim version without models (faster build)
docker compose --profile slim up -d comfyui-wan22-gguf-slim
```

### Option 2: Direct Docker Build

```bash
# Build with model downloads
docker build -f Dockerfile.optimized -t comfyui-wan22-gguf:latest .

# Build without models (faster)
docker build -f Dockerfile.optimized \
  --build-arg DOWNLOAD_MODELS=false \
  -t comfyui-wan22-gguf:slim .
```

### Option 3: Manual Model Management

If you want to manage models separately:

```bash
# Create models directory
mkdir -p ./models

# Download models manually (faster than during build)
cd models
wget -c https://huggingface.co/kwaikeg/WAN2.2-14B-I2V/resolve/main/wan2.2-14b-i2v-q4ks.gguf
wget -c https://huggingface.co/kwaikeg/WAN2.2-14B-I2V/resolve/main/text_encoder.safetensors
wget -c https://huggingface.co/kwaikeg/WAN2.2-14B-I2V/resolve/main/scheduler_config.json
wget -c https://huggingface.co/kwaikeg/WAN2.2-14B-I2V/resolve/main/model_index.json

# Build slim version
docker build -f Dockerfile.optimized \
  --build-arg DOWNLOAD_MODELS=false \
  -t comfyui-wan22-gguf:slim .

# Run with mounted models
docker run -d \
  --name comfyui-wan22-gguf \
  --gpus all \
  -p 8188:8188 \
  -v $(pwd)/models:/app/ComfyUI/models/wan2.2 \
  -v $(pwd)/output:/app/ComfyUI/output \
  comfyui-wan22-gguf:slim
```

## Build Options

### Build Arguments

- `DOWNLOAD_MODELS=true` - Download WAN2.2 models during build (default: true)
- `MODEL_BASE_URL` - Base URL for model downloads (default: HuggingFace)

### Environment Variables

- `CUDA_VISIBLE_DEVICES` - GPU selection (default: 0)
- `PYTORCH_CUDA_ALLOC_CONF` - CUDA memory management (default: max_split_size_mb:512)

## System Requirements

### Hardware
- NVIDIA GPU with 16GB+ VRAM (recommended: RTX 3090/4090, A100)
- 32GB+ RAM
- 100GB+ free disk space (for models)

### Software
- Docker with NVIDIA Container Toolkit
- CUDA 12.8+ drivers
- Docker Compose v2+

## Performance Optimization

### GPU Memory Optimization
The container sets `PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512` to prevent memory fragmentation.

### Model Storage
- Models total ~25GB+ (GGUF format)
- Use SSD storage for better I/O performance
- Consider mounting models from fast external storage

## Troubleshooting

### Build Issues
```bash
# If build fails during model download, retry with:
docker build --no-cache -f Dockerfile.optimized .

# Or skip models and download separately:
docker build --build-arg DOWNLOAD_MODELS=false -f Dockerfile.optimized .
```

### Runtime Issues
```bash
# Check GPU availability
docker run --rm --gpus all nvidia/cuda:12.8-base nvidia-smi

# Check container logs
docker logs comfyui-wan22-gguf

# Test ComfyUI API
curl http://localhost:8188/
```

### Memory Issues
- Reduce batch sizes in workflows
- Use lower resolution inputs
- Monitor GPU memory with `nvidia-smi`
- Consider using FP16 or lower precision

## Accessing ComfyUI

Once running, access ComfyUI at:
- **WebUI**: http://localhost:8188
- **API**: http://localhost:8188/api/v1/

## Model Information

The WAN2.2-14B GGUF model provides:
- **Quantization**: Q4KS (4-bit quantized with K-scaling)
- **Parameters**: 14 billion
- **Task**: Image-to-Video generation
- **Input Resolution**: 512x512 to 1024x1024
- **Output**: Video sequences up to 16 frames

## Volume Mounts

Recommended volume mounts:
- `./models:/app/ComfyUI/models/wan2.2` - Model storage
- `./output:/app/ComfyUI/output` - Generated videos
- `./input:/app/ComfyUI/input` - Input images
- `./workflows:/app/ComfyUI/custom_workflows` - Custom workflows

## Security Notes

- Container runs as non-root user `comfyui`
- GPU access is restricted to compute capabilities only
- No external network access during model loading
- Health checks ensure service availability

## Comparison with Original

This reverse-engineered version aims to match the functionality of `nykk3/comfyui-wan2.2-gguf:q4ks-14b-i2v-cuda12.8` while providing:

- ✅ Better build optimization and layer caching
- ✅ Multi-stage builds for faster iterations
- ✅ Configurable model downloads
- ✅ Comprehensive documentation
- ✅ Security improvements (non-root user)
- ✅ Flexible volume mounting
- ✅ Health checks and monitoring