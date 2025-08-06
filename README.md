# WAN2.2 I2V Rapid - RunPod API

WAN2.2 Image-to-Video generation model deployed as a RunPod serverless API.

## Overview

This repository provides a RunPod-compatible API wrapper for the [Wan2.2](https://github.com/Wan-Video/Wan2.2) image-to-video generation model. It supports high-quality I2V generation with rapid processing using the WAN2.2-14B-Rapid-AllInOne model.

## Features

- **High-Quality Video Generation**: 720p/480p video output at 24fps
- **Rapid Processing**: Optimized for fast inference with FP8 quantization
- **RunPod Compatible**: Full serverless deployment support
- **Local Development**: Docker Compose setup for local testing
- **Flexible Input**: Supports various image formats and prompting

## Model Information

- **Model**: [WAN2.2-14B-Rapid-AllInOne](https://huggingface.co/Phr00t/WAN2.2-14B-Rapid-AllInOne)
- **Paper**: [WAN2.2: Revolutionizing Video Generation](https://arxiv.org/abs/2503.20314)
- **Framework**: ComfyUI with custom WAN nodes
- **Hardware**: NVIDIA GPU with 20GB+ VRAM recommended

## API Parameters

### Input Schema

```json
{
  "input_image": "https://example.com/image.jpg",
  "positive_prompt": "A beautiful landscape with dynamic movement",
  "negative_prompt": "static, blurry, low quality",
  "crop": "center",
  "width": 720,
  "height": 480,
  "length": 53,
  "batch_size": 1,
  "shift": 8.0,
  "cfg": 1.0,
  "sampler_name": "lcm",
  "scheduler": "beta",
  "steps": 4,
  "seed": 0,
  "fps": 24
}
```

### Parameters Description

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_image` | string | required | URL of the input image |
| `positive_prompt` | string | required | Prompt describing desired video content |
| `negative_prompt` | string | "" | Prompt describing undesired content |
| `crop` | string | "center" | Image cropping method |
| `width` | integer | 720 | Output video width (480/720/1024/1280) |
| `height` | integer | 480 | Output video height (480/720/1024/1280) |
| `length` | integer | 53 | Video length in frames |
| `batch_size` | integer | 1 | Number of videos to generate |
| `shift` | float | 8.0 | Model sampling shift parameter |
| `cfg` | float | 1.0 | Classifier-free guidance scale |
| `sampler_name` | string | "lcm" | Sampling method |
| `scheduler` | string | "beta" | Noise scheduler |
| `steps` | integer | 4 | Number of inference steps |
| `seed` | integer | 0 | Random seed (0 for random) |
| `fps` | integer | 24 | Output video frame rate |

### Output Format

```json
{
  "jobId": "job-12345",
  "result": "/path/to/output/video.mp4",
  "status": "DONE",
  "message": "Video saved locally",
  "execution_time": 88.36
}
```

## RunPod Deployment

### 1. Deploy to RunPod Serverless

1. Fork this repository
2. Create a new RunPod Serverless endpoint
3. Configure the endpoint:
   - **Container Image**: Use the built Docker image
   - **GPU**: RTX 3090/4090 or A5000+ (20GB+ VRAM)
   - **Container Start Command**: `python worker_runpod.py`

### 2. API Usage

```bash
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "input_image": "https://example.com/image.jpg",
      "positive_prompt": "A serene lake with gentle ripples"
    }
  }'
```

### 3. Check Job Status

```bash
curl -X GET "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/status/JOB_ID" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Local Development

### Prerequisites

- Docker with GPU support (NVIDIA Docker)
- NVIDIA GPU with 20GB+ VRAM
- 100GB+ free disk space

### Quick Start with Docker Compose

1. **Clone the repository**:
   ```bash
   git clone https://github.com/camenduru/wan2.2-i2v-rapid-tost.git
   cd wan2.2-i2v-rapid-tost
   ```

2. **Start the local development server**:
   ```bash
   docker compose up --build
   ```

3. **Test with the CLI tool**:
   ```bash
   # Using the host CLI tool (recommended)
   ./cli.py -i input.jpg -p "A beautiful scene" -w 576 --height 576
   
   # Or test the API directly with curl
   curl -X POST http://localhost:8080/run \
     -H "Content-Type: application/json" \
     -d @test_input.json
   ```

4. **Check generated videos**:
   ```bash
   ls -la output/
   ```

### Manual Docker Build & Run

1. **Build the Docker image**:
   ```bash
   docker build -t wan2.2-i2v-local .
   ```

2. **Run with test input**:
   ```bash
   docker run --gpus all --rm \
     -v $(pwd)/test_input.json:/content/ComfyUI/test_input.json \
     -v $(pwd)/output:/content/ComfyUI/output \
     wan2.2-i2v-local python worker_runpod.py
   ```

3. **Run API server**:
   ```bash
   docker run --gpus all -p 8080:8080 \
     -v $(pwd)/output:/content/ComfyUI/output \
     wan2.2-i2v-local python worker_runpod.py --rp_serve_api --rp_api_host=0.0.0.0
   ```

### Using the Host CLI Tool (Recommended)

The CLI tool runs on your host machine and sends requests to the Docker API server:

1. **Start the API servers**:
   ```bash
   docker compose up -d
   ```

2. **Generate videos using the CLI**:
   ```bash
   # Auto-detect resolution (maintains aspect ratio, default behavior)
   ./cli.py -i girl1.jpg -p "Gentle portrait with soft movement" -n "mouth opening, talking"
   
   # Manual resolution specification
   ./cli.py -i input.jpg -p "Beautiful flowing water" -w 720 --height 480 --no-auto-resize
   
   # Using synchronous mode (wait for completion)
   ./cli.py --sync -i landscape.jpg -p "Serene landscape with wind"
   
   # With environment variables
   INPUT_IMAGE=my_image.jpg POSITIVE_PROMPT="Dynamic scene" ./cli.py
   ```

3. **FLF (First-Last Frame) generation**:
   ```bash
   # Basic FLF generation (uses port 8081)
   ./flf/cli.py -i start.jpg -e end.jpg -p "Smooth transition between frames" -w 576 --height 576 -l 81
   
   # With custom API URL
   ./flf/cli.py --api-url http://localhost:8081 -i girl1.jpg -e girl2.jpg
   ```

### Using Local Images

You can use local images instead of URLs. Place your images in the `input/` directory and reference them by filename:

1. **Add your image to the input directory**:
   ```bash
   cp your_image.jpg input/
   ```

2. **Generate with local image**:
   ```bash
   # Make sure the API server is running
   docker compose up -d
   
   # Use the CLI tool
   ./cli.py -i input/your_image.jpg -p "Your prompt here"
   ```

### Available Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `INPUT_IMAGE` | URL | Image URL or local filename |
| `POSITIVE_PROMPT` | "A beautiful scene..." | Desired video content description |
| `NEGATIVE_PROMPT` | "static, blurry..." | Undesired content description |
| `WIDTH` | 720 | Video width (480/720/1024/1280) |
| `HEIGHT` | 480 | Video height (480/720/1024/1280) |
| `STEPS` | 4 | Number of inference steps |
| `SEED` | 42 | Random seed (for reproducibility) |
| `FPS` | 24 | Output video frame rate |
| `LENGTH` | 53 | Video length in frames |
| `CFG` | 1.0 | Classifier-free guidance scale |
| `SHIFT` | 8.0 | Model sampling shift parameter |

### Image Input Options

The `INPUT_IMAGE` parameter supports:
- **URLs**: `"https://example.com/image.jpg"`
- **Local filenames**: `"my_image.png"` (from `input/` directory)
- **Absolute paths**: `"/path/to/image.jpg"`

### Testing with Different Parameters

Edit `test_input.json` or create custom configuration files:

### CLI Tool Arguments

```bash
./cli.py -h  # Show all options

# Most commonly used arguments:
-i, --input-image     Input image path or URL
-p, --positive-prompt Text describing desired video content
-n, --negative-prompt Text describing undesired content
-w, --width          Video width (default: 720)
--height             Video height (default: 480)
-l, --length         Video length in frames (default: 53)
-s, --steps          Inference steps (default: 4)
--seed               Random seed for reproducibility
--fps                Frames per second (default: 24)
--sync               Use synchronous API (wait for completion)
--api-url            Custom API server URL (default: http://localhost:8080)
--auto-resize        Auto-detect image dimensions and maintain aspect ratio (default: True)
--no-auto-resize     Disable automatic resolution detection

# FLF-specific arguments:
-i, --start-image    Start image for transition
-e, --end-image      End image for transition

# Resolution Auto-Detection:
The CLI automatically detects input image dimensions and scales them to fit within
VRAM limits while preserving aspect ratio. This avoids unwanted square videos.
- Horizontal images (wide): Max 720x480
- Vertical images (tall): Max 480x720  
- Square-ish images: Max 576x576
```

### Direct API Usage (Alternative)

If you prefer to use the API directly:

```bash
# Asynchronous request
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "input_image": "girl1.jpg",
      "positive_prompt": "Beautiful scene",
      "negative_prompt": "static, blurry",
      "crop": "center",
      "width": 576,
      "height": 576,
      "length": 72,
      "steps": 4,
      "seed": 42
    }
  }'

# Check status
curl http://localhost:8080/status/{job_id}
```

## Performance Notes

- **Memory Usage**: ~20GB VRAM for 720p generation
- **Generation Time**: ~2-5 minutes per video (depending on resolution/steps)
- **Supported Resolutions**: 480p, 720p, 1024p, 1280p
- **Recommended Settings**: 720x480, 4 steps for optimal speed/quality balance

## Model Architecture

This implementation uses:
- **WAN2.2 14B Model**: Main video generation model
- **VAE**: Wan2.2-VAE for video encoding/decoding  
- **Text Encoder**: UMT5-XXL for text processing
- **CLIP Vision**: For image understanding
- **FP8 Quantization**: For memory efficiency

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**:
   - Reduce resolution (720x480 instead of 1280x720)
   - Use fewer inference steps
   - Ensure no other GPU processes are running

2. **Model Loading Errors**:
   - Verify NVIDIA drivers are installed
   - Check Docker GPU support: `docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi`

3. **Slow Generation**:
   - Use LCM sampler with 4 steps
   - Enable FP8 quantization
   - Ensure sufficient GPU memory

### Debug Mode

Run with debug logging:

```bash
docker run --gpus all -e PYTHONUNBUFFERED=1 \
  -v $(pwd)/output:/content/ComfyUI/output \
  wan2.2-i2v-local python worker_runpod.py --rp_log_level=DEBUG
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Test locally with Docker Compose
4. Submit a pull request

## License

This project follows the original WAN2.2 model licensing terms. Please refer to the [official repository](https://github.com/Wan-Video/Wan2.2) for details.

## Credits

- **WAN2.2 Model**: [Wan-Video Team](https://github.com/Wan-Video/Wan2.2)
- **ComfyUI Integration**: [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- **RunPod Deployment**: [camenduru](https://github.com/camenduru)