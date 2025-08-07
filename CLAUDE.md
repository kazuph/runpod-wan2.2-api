# WAN2.2 I2V Video Generation - Knowledge Base

****************rapid-i2v禁止**********************
****************rapid-i2v禁止**********************
****************rapid-i2v禁止**********************
****************flf/以下での作業禁止**********************
****************flf/以下での作業禁止**********************
****************flf/以下での作業禁止**********************
****************wan2.1禁止、wan2.2のみ許可*********************
****************wan2.1禁止、wan2.2のみ許可*********************
****************wan2.1禁止、wan2.2のみ許可*********************

This document contains key insights and best practices for generating high-quality videos using the WAN2.2 I2V (Image-to-Video) model.

## Model Information

- **Model**: WAN2.2 I2V A14B (14 billion parameters)
- **Architecture**: Mixture-of-Experts (MoE) with improved stability
- **Supported Resolutions**: 480P (recommended), 720P, custom sizes
- **Framework**: ComfyUI
- **Hardware Requirements**: NVIDIA GPU with CUDA support

## GPU Memory Management

### Memory Constraints
- **RTX 3090 (24GB)**: Maximum tested resolution 720x720 for 3-5 second videos
- **Memory Allocation Issues**: 
  - 1024x576+ causes CUDA out of memory errors
  - Vertical videos >720 height often fail
  - Sequential generation recommended over parallel

### Optimal Resolutions
- **Square**: 720x720 (stable, good quality)
- **Horizontal**: 720x480 (16:9 aspect ratio)
- **Vertical**: 480x720 (9:16 aspect ratio, mobile-friendly)
- **Small formats**: 576x576 for complex scenes

### GPU Memory Safe Resolutions (RTX 3090 24GB)
- **✅ Safe (No OOM errors)**:
  - 576x576 (3-5 seconds) - Most reliable
  - 720x480 (3-4 seconds) - Horizontal videos
  - 480x720 (3-4 seconds) - Vertical videos
  - 720x720 (3 seconds) - Square, shorter duration only

- **⚠️ Risky (May cause OOM)**:
  - 720x720 (4-5 seconds) - Often fails
  - 1024x576 - Usually fails
  - 1024x720+ - Always fails
  - Any resolution >720 in both dimensions

- **💡 Memory Optimization Tips**:
  - Use 576x576 for longest videos (up to 5 seconds)
  - Reduce duration if using 720x720
  - Sequential generation only (never parallel)
  - Restart Docker container if experiencing repeated OOM errors

## Video Duration Settings

### Frame Length Calculation
- **3 seconds**: `length: 72` (24 fps × 3)
- **4 seconds**: `length: 96` (24 fps × 4) 
- **5 seconds**: `length: 120` (24 fps × 5)

### Recommended Settings
```json
{
  "fps": 24,
  "shift": 8.0,
  "cfg": 1.0,
  "sampler_name": "lcm",
  "scheduler": "beta",
  "steps": 4
}
```

## Image Preprocessing

### Background Issues
- **Transparent backgrounds cause poor results**
- **Solution**: Convert to white background before processing
```python
# Convert transparent to white background
white_bg = Image.new('RGB', img.size, (255, 255, 255))
if img.mode in ('RGBA', 'LA'):
    img = img.convert('RGBA')
    white_bg.paste(img, (0, 0), img)
```

### Aspect Ratio Preservation (Auto-Detection)
- **CLI tools automatically detect input image dimensions and preserve aspect ratio**
- **Square videos (576x576) are avoided unless the input is square**
- Resolution is automatically scaled to fit within VRAM limits:
  - Horizontal/wide images → max 720x480
  - Vertical/tall images → max 480x720
  - Square-ish images → max 576x576
- Use `--no-auto-resize` to disable auto-detection
- Manual resolution can be specified with `-w` and `--height`

## Prompt Engineering

### Preventing Mouth Movement (Critical Issue)
WAN2.2 has a tendency to generate unwanted mouth/lip movement. Combat this with:

**Positive Prompts for Static Faces:**
```
"Close-up portrait with serene expression, closed lips, direct eye contact with camera, natural lighting, minimal movement, static pose, calm demeanor, peaceful countenance, steady gaze"
```

**Negative Prompts (Essential):**
```
"mouth opening, lip movement, talking, speaking, facial animation, lip sync, dialogue, conversation, mouth motion, jaw movement, teeth showing, tongue visible"
```

### Action-Specific Prompts

**Figure Skating:**
```
"Beautiful figure skating performance, graceful spinning motion, elegant ice skating routine, dynamic twirling movement, artistic ice dance, flowing costume movement"
```

**Combat/Action:**
```
"Epic combat scene, weapon firing, muzzle flash, weapon recoil, dynamic action sequence, tactical stance, intense battle atmosphere"
```

**Character Animation:**
```
"Energetic waving enthusiastically, cheerful gesture, dynamic hand movements, animated greeting, positive atmosphere"
```

### Prompt Structure Best Practices
1. **Focus on one main action** per generation
2. **Be specific about body parts** and movements
3. **Use natural language** rather than keyword stuffing
4. **Describe lighting and atmosphere** for better quality
5. **Always include mouth/speech prevention** in negatives

## Technical Configuration

### Docker Setup
```bash
# Start API servers with Docker Compose
docker compose up -d

# Check running containers
docker ps | grep wan2

# View logs
docker compose logs -f wan2-i2v
```

### CLI Usage (Recommended)
```bash
# Auto-detect resolution from input image (maintains aspect ratio)
./cli.py -i input.jpg -p "Your prompt" -n "negative prompt"

# Manual resolution (disables auto-detection)
./cli.py -i input.jpg -p "Your prompt" -w 576 --height 576 --no-auto-resize

# For FLF generation (port 8081) - auto-detects from start image
./flf/cli.py -i start.jpg -e end.jpg -p "transition prompt"

# Synchronous mode (wait for completion)
./cli.py --sync -i input.jpg -p "Beautiful scene"
```

### Environment Variables

The CLI tools support environment variables as fallbacks:

```bash
INPUT_IMAGE=input_001.png
POSITIVE_PROMPT="Beautiful scene with gentle movement"
NEGATIVE_PROMPT="mouth opening, talking, speaking"
WIDTH=720
HEIGHT=720
LENGTH=72
SEED=101

# Run with environment variables
./cli.py  # Will use the environment variables
```

### Sample Configurations

### Command Line Arguments (Recommended)

**Static Portrait (3 seconds):**
```bash
./cli.py \
  -i "input_001_white.png" \
  -p "Close-up portrait with serene expression, closed lips, direct eye contact with camera, natural lighting, minimal movement, static pose, calm demeanor" \
  -n "mouth opening, lip movement, talking, speaking, facial animation, lip sync, dialogue, conversation" \
  -w 720 --height 720 -l 72
```

**Fireworks Celebration (5 seconds):**
```bash
./cli.py \
  -i "image_005_black.png" \
  -p "Beautiful fireworks exploding in night sky above children, colorful fireworks bursting and sparkling, magical firework display, bright colorful explosions" \
  -n "mouth opening, talking, speaking, facial animation, daytime, bright lighting, no fireworks, static sky" \
  -w 576 --height 576 -l 120
```

### Environment Variables (Alternative)

**Static Portrait (3 seconds):**
```bash
export INPUT_IMAGE="input_001_white.png"
export POSITIVE_PROMPT="Close-up portrait with serene expression, closed lips, direct eye contact with camera, natural lighting, minimal movement, static pose, calm demeanor"
export NEGATIVE_PROMPT="mouth opening, lip movement, talking, speaking, facial animation, lip sync, dialogue, conversation"
export WIDTH=720
export HEIGHT=720
export LENGTH=72
./cli.py
```

**Fireworks Celebration (5 seconds):**
```bash
export INPUT_IMAGE="image_005_black.png"
export POSITIVE_PROMPT="Beautiful fireworks exploding in night sky above children, colorful fireworks bursting and sparkling, magical firework display, bright colorful explosions"
export NEGATIVE_PROMPT="mouth opening, talking, speaking, facial animation, daytime, bright lighting, no fireworks, static sky"
export WIDTH=576
export HEIGHT=576
export LENGTH=120
./cli.py
```

## Common Issues & Solutions

### 1. CUDA Out of Memory
- **Reduce resolution**: Try 576x576 or 480x720
- **Shorter duration**: Reduce length parameter
- **Sequential processing**: Generate one video at a time

### 2. Unwanted Mouth Movement
- **Add comprehensive negative prompts** about speech/talking
- **Use "closed lips, serene expression"** in positive prompts
- **Avoid emotion words** that might trigger facial animation

### 3. Static/Boring Results
- **Be specific about the desired action**
- **Use dynamic descriptive words**: "graceful", "flowing", "energetic"
- **Include environmental context**: lighting, atmosphere

### 4. Poor Quality/Artifacts
- **Check input image quality** and background
- **Ensure proper aspect ratio** matching
- **Adjust CFG guidance** (keep around 1.0 for LCM)

## File Size Expectations

- **3-second 720x720**: ~300-500KB
- **5-second 720x480**: ~1.2MB
- **5-second 576x576**: ~180KB

## Workflow Summary

1. **Read and analyze input images**: Always use Read tool to understand image content, subjects, composition, and background before processing
2. **Prepare input images**: Convert transparent backgrounds to white
3. **Choose appropriate dimensions**: Based on content and GPU memory
4. **Craft prompts carefully**: Include action description + mouth prevention
5. **Set duration and technical parameters**
6. **Generate sequentially**: Avoid parallel processing for memory management
7. **Verify output quality**: Check for unwanted artifacts or mouth movement

## Best Practices Checklist

- [ ] Input image analyzed using Read tool to understand content
- [ ] Input image has solid background (not transparent)
- [ ] Let CLI auto-detect resolution to preserve aspect ratio (avoid square videos)
- [ ] Only specify manual resolution if specific size needed
- [ ] Prompt includes specific action description
- [ ] Negative prompt includes mouth/speech prevention
- [ ] Duration set appropriately (72-120 frames typical)
- [ ] Technical settings optimized (cfg=1.0, steps=4)
- [ ] Sequential generation for multiple videos

This knowledge base should be updated as new insights are discovered through continued experimentation with the WAN2.2 model.

## Development Guidelines

### ⚠️ CRITICAL DOCKER RULES - MUST READ ⚠️

#### 🚫 ABSOLUTELY FORBIDDEN ACTIONS 🚫

1. **NEVER USE `docker run` COMMAND**
   - **THIS IS STRICTLY PROHIBITED!** This project REQUIRES GPU access
   - **ALWAYS use `docker compose` commands ONLY**
   - The docker-compose.yml is configured with proper GPU settings
   - Using `docker run` will FAIL because it lacks GPU configuration

2. **NEVER DELETE DOCKER IMAGES OR BUILD WITHOUT CACHE**
   - **DO NOT remove Docker images** - They contain critical build cache
   - **DO NOT run `docker image prune` or `docker system prune -a`**
   - **DO NOT use `--no-cache` flag when building**
   - **DO NOT use `docker rmi` to remove images**
   - Build times can exceed **1 HOUR** - image layers are CRITICAL
   - **Past incidents have wasted DAYS due to image cache loss**
   - Note: Containers can be removed safely, but NEVER remove images
   
   **今後は以下を厳守します：**
   - ❌ **docker rmi** - イメージ削除禁止
   - ❌ **docker image prune** - イメージクリーンアップ禁止
   - ❌ **--no-cache** - キャッシュなしビルド禁止
   - ❌ **docker system prune -a** - システム全体のクリーンアップ禁止

#### ✅ MANDATORY GPU CONFIGURATION

All Docker operations MUST include GPU support:
```yaml
# Required in docker-compose.yml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

#### ✅ CORRECT USAGE

**ALWAYS use docker compose commands with ghost run wrapper:**
```bash
# Start services (CORRECT)
ghost run -- docker compose up -d

# View logs (CORRECT)
ghost run -- docker compose logs -f

# Rebuild with cache (CORRECT - MUST use ghost run)
ghost run -- docker compose build

# Stop services without removing (CORRECT)
ghost run -- docker compose stop
```

**NEVER use these commands:**
```bash
# ❌ FORBIDDEN - No GPU access
docker run [any arguments]

# ❌ FORBIDDEN - Destroys build cache
docker compose build --no-cache
ghost run -- docker compose build --no-cache

# ❌ FORBIDDEN - Removes images (CRITICAL!)
docker rmi [any image]  # 絶対禁止！イメージ削除は致命的
docker image prune

# ❌ FORBIDDEN - Cleans images and build cache
docker system prune -a
```

**Safe to use:**
```bash
# ✅ OK - Remove containers only (keeps images)
docker compose down
docker container prune

# ✅ OK - Remove volumes if needed
docker volume prune
```

### ⚠️ DOCKERFILE MODIFICATION RULES ⚠️

#### 📝 CRITICAL: Dockerfile Edit Guidelines

1. **DOCKER EXEC IS FOR REFERENCE ONLY**
   - **`docker exec` commands are ONLY for inspecting/checking container state**
   - **NEVER use `docker exec` to modify files or install packages**
   - **All changes MUST be made in the Dockerfile itself**

2. **MODIFY ONLY THE BOTTOM OF DOCKERFILE**
   - **NEVER modify the upper parts of Dockerfile** - They contain critical base layers
   - **Add new instructions at the BOTTOM, just before the final WORKDIR**
   - **If new downloads/installations are needed, add them BEFORE the final WORKDIR**
   - **Dockerfile redundancy is NOT a problem** - Prioritize cache preservation

3. **PRESERVE BUILD CACHE AT ALL COSTS**
   - **Add new RUN commands as separate layers** - Don't combine with existing ones
   - **Place new package installations at the end** - Before WORKDIR
   - **Example structure:**
     ```dockerfile
     # ... existing layers (DO NOT TOUCH) ...
     
     # New additions go here (before final WORKDIR)
     RUN pip install new-package
     RUN apt-get update && apt-get install -y new-tool
     
     # Final WORKDIR (keep at the very end)
     WORKDIR /workspace
     ```

### Docker Command Execution
- **All build and inference Docker commands must be run via `ghost run`**
- This ensures proper background execution and process management
- Example: `ghost run -- docker compose build` instead of `docker compose build`

### FLF (First-Last Frame) Operations
- **Always execute FLF commands from the `flf/` directory**: `cd flf && ghost run -- [command]`
- **Output is automatically saved to `flf/output/`** via Docker volume mounting
- **Use WanFirstLastFrameToVideo node** for 2-image transitions
- **FLF requires both start_image and end_image parameters**

### Code Architecture Principles
- **Never create temporary files for inference operations**
- **All functionality must be implemented in permanent code files**
- **Parameter changes should handle all variations without new file creation**
- **Avoid one-off scripts - build reusable components with parameter support**
- This ensures operational scalability and maintenance efficiency

### RunPod Serverless Deployment
- **All projects must ultimately run on RunPod Serverless platform**
- **Local testing must be configured using Docker Compose environment**
- **Reference**: Follow the RunPod local testing guide at https://docs.runpod.io/serverless/development/local-testing
- **Important**: Ensure your Docker Compose setup matches RunPod's serverless requirements for proper local testing and seamless deployment


****************rapid-i2v禁止**********************
****************rapid-i2v禁止**********************
****************rapid-i2v禁止**********************
****************flf/以下での作業禁止**********************
****************flf/以下での作業禁止**********************
****************flf/以下での作業禁止**********************
****************wan2.1禁止、wan2.2のみ許可*********************
****************wan2.1禁止、wan2.2のみ許可*********************
****************wan2.1禁止、wan2.2のみ許可*********************
