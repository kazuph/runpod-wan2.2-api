# ComfyUI WAN2.2 Workflows

This directory contains Docker setup and workflows for running ComfyUI with WAN2.2 models.

## Directory Structure

```
comfyui_workflow/
├── Dockerfile              # ComfyUI Docker image with CUDA support
├── docker-compose.yml      # Docker Compose configuration
├── README.md              # This file
├── workflows/             # WAN2.2 workflow JSON files
│   ├── text_to_video_wan22_5B.json
│   ├── image_to_video_wan22_5B.json
│   ├── text_to_video_wan22_14B.json
│   └── image_to_video_wan22_14B.json
├── models/                # Models directory (mounted volume)
├── input/                 # Input images/videos
└── output/                # Generated outputs
```

## Required Models

You need to download the following models and place them in the correct directories:

### Text Encoder (place in `models/text_encoders/`)
- `umt5_xxl_fp8_e4m3fn_scaled.safetensors`

### VAE Files (place in `models/vae/`)
- For 14B models: `wan_2.1_vae.safetensors`
- For 5B model: `wan2.2_vae.safetensors`

### Diffusion Models (place in `models/diffusion_models/`)

**5B Model:**
- `wan2.2_ti2v_5B_fp16.safetensors`

**14B Text-to-Video:**
- `wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors`
- `wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors`

**14B Image-to-Video:**
- `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors`
- `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors`

## Usage

1. **Build and start the container:**
   ```bash
   docker compose up -d --build
   ```

2. **Access ComfyUI:**
   - Open your browser to `http://localhost:8188`

3. **Load workflows:**
   - Drag and drop any of the JSON files from the `workflows/` directory into ComfyUI
   - The workflows are pre-configured for their respective models

4. **Model placement:**
   - Models are cached in `~/.cache` (mounted volume)
   - Place downloaded models in the `models/` directory structure as described above

## Workflows

- **text_to_video_wan22_5B.json**: Text-to-video generation using 5B model
- **image_to_video_wan22_5B.json**: Image-to-video generation using 5B model  
- **text_to_video_wan22_14B.json**: Text-to-video generation using 14B model
- **image_to_video_wan22_14B.json**: Image-to-video generation using 14B model

## GPU Requirements

- NVIDIA GPU with CUDA support
- Minimum 12GB VRAM for 5B models
- Recommended 24GB+ VRAM for 14B models

## Troubleshooting

- If you encounter CUDA out of memory errors, try using the 5B models instead of 14B
- Ensure all required models are downloaded and placed in the correct directories
- Check container logs: `docker compose logs -f comfyui-wan22`