# WAN2.2 I2V Video Generation - Knowledge Base

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

### Aspect Ratio Preservation
- Input image aspect ratio should match output video dimensions
- Use `crop: "center"` for automatic cropping
- Consider content placement when choosing dimensions

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
# Build image
docker build -t wan2.2-i2v-local .

# Run with GPU support
docker run --rm --gpus all \
  -v "$(pwd)/input:/content/ComfyUI/input" \
  -v "$(pwd)/output:/content/ComfyUI/output" \
  wan2.2-i2v-local
```

### API Usage
```bash
# Local server endpoint
curl -X POST http://localhost:8080/runsync \
  -H 'Content-Type: application/json' \
  -d '{"input": {...}}'
```

### Environment Variables
```bash
INPUT_IMAGE=input_001.png
POSITIVE_PROMPT="Beautiful scene with gentle movement"
NEGATIVE_PROMPT="mouth opening, talking, speaking"
WIDTH=720
HEIGHT=720
LENGTH=72
SEED=101
```

### Sample Configurations

### Command Line Arguments (Recommended)

**Static Portrait (3 seconds):**
```bash
docker compose run --rm wan2-i2v python generate_video.py \
  -i "input_001_white.png" \
  -p "Close-up portrait with serene expression, closed lips, direct eye contact with camera, natural lighting, minimal movement, static pose, calm demeanor" \
  -n "mouth opening, lip movement, talking, speaking, facial animation, lip sync, dialogue, conversation" \
  -w 720 --height 720 -l 72
```

**Fireworks Celebration (5 seconds):**
```bash
docker compose run --rm wan2-i2v python generate_video.py \
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
docker compose run --rm wan2-i2v python generate_video.py
```

**Fireworks Celebration (5 seconds):**
```bash
export INPUT_IMAGE="image_005_black.png"
export POSITIVE_PROMPT="Beautiful fireworks exploding in night sky above children, colorful fireworks bursting and sparkling, magical firework display, bright colorful explosions"
export NEGATIVE_PROMPT="mouth opening, talking, speaking, facial animation, daytime, bright lighting, no fireworks, static sky"
export WIDTH=576
export HEIGHT=576
export LENGTH=120
docker compose run --rm wan2-i2v python generate_video.py
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
- [ ] Resolution chosen based on GPU memory constraints
- [ ] Prompt includes specific action description
- [ ] Negative prompt includes mouth/speech prevention
- [ ] Duration set appropriately (72-120 frames typical)
- [ ] Technical settings optimized (cfg=1.0, steps=4)
- [ ] Sequential generation for multiple videos

This knowledge base should be updated as new insights are discovered through continued experimentation with the WAN2.2 model.