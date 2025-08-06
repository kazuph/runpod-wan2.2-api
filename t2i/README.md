# WAN2.1 T2I (Text-to-Image) API

This directory contains a WAN2.1 T2I implementation for generating static images from text prompts.

## Current Status

- ✅ Docker container built with all WAN2.1 models downloaded
- ✅ API server running on port 8083
- ⚠️ Test mode implementation (generates gradient images with overlays)
- ❌ WAN2.1 model loading not yet functional due to ComfyUI node initialization issues

## Models Downloaded

- `umt5-xxl-enc-bf16.safetensors` (10GB) - Text encoder
- `Wan2_1-T2V-14B_fp8_e4m3fn.safetensors` (13GB) - Main diffusion model
- `Wan2_1_VAE_bf16.safetensors` (242MB) - VAE decoder
- `Wan2_1-VACE_module_14B_fp8_e4m3fn.safetensors` - VACE enhancement module

## Usage

### Start the container:
```bash
docker compose up -d
```

### Generate images using the CLI:
```bash
# Basic generation
./cli.py -p "Your prompt here"

# With custom parameters
./cli.py -p "A beautiful landscape" -n "blurry, low quality" -w 720 --height 480 --seed 42

# Synchronous mode (wait for completion)
./cli.py --sync -p "Your prompt here"
```

### Environment variables (optional):
```bash
export POSITIVE_PROMPT="A beautiful mountain landscape"
export NEGATIVE_PROMPT="blurry, low quality"
export WIDTH=576
export HEIGHT=576
export STEPS=20
export CFG=7.0
export SEED=42
./cli.py
```

## API Endpoints

- POST `/run` - Asynchronous generation
- POST `/runsync` - Synchronous generation
- GET `/status/{job_id}` - Check job status

## Known Issues

1. **WanVideo Node Loading**: The ComfyUI-WanVideoWrapper custom nodes fail to load properly due to module import issues
2. **Model Inference**: Currently only generates test gradient images, not actual AI-generated images
3. **Memory Requirements**: The 14B model requires significant VRAM (>20GB) even with FP8 quantization

## Next Steps

To enable actual WAN2.1 inference:

1. Fix the ComfyUI custom node loading mechanism
2. Properly initialize the WanVideo nodes
3. Implement the full inference pipeline
4. Add proper error handling and model state management

## Output Location

Generated images are saved to:
- Container: `/content/ComfyUI/output/`
- Host: `./output/` (when copied manually)