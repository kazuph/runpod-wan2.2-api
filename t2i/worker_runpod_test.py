#!/usr/bin/env python3
"""
Simplified RunPod worker for testing T2I generation in test mode.
This version skips the problematic WanVideo node loading and uses test mode only.
"""
import os
import json
import random
import runpod
from PIL import Image, ImageDraw, ImageFont

def generate_test_image(prompt, seed=None, width=768, height=768):
    """Generate a test image with the prompt text"""
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    
    # Create a test image with the prompt text
    img = Image.new('RGB', (width, height), color='darkblue')
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    # Draw the prompt
    text = f"Test Mode\n\nPrompt: {prompt[:50]}...\nSeed: {seed}\nSize: {width}x{height}"
    draw.multiline_text((10, 10), text, fill='white', font=font)
    
    # Save
    filename = f"test_{seed}.png"
    filepath = os.path.join("/content/ComfyUI/output", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    img.save(filepath)
    
    return filename

def handler(job):
    """RunPod handler function"""
    try:
        job_input = job['input']
        
        # Extract parameters
        prompt = job_input.get('prompt', 'A beautiful landscape')
        negative_prompt = job_input.get('negative_prompt', '')
        width = job_input.get('width', 768)
        height = job_input.get('height', 768)
        steps = job_input.get('steps', 4)
        cfg = job_input.get('cfg', 1.0)
        seed = job_input.get('seed', None)
        
        print(f"Generating test image: {prompt} ({width}x{height})")
        
        # Generate test image
        filename = generate_test_image(
            prompt=prompt,
            seed=seed,
            width=width,
            height=height
        )
        
        # Return result
        return {
            "status": "success",
            "output": {
                "filename": filename,
                "seed": seed if seed else "random",
                "mode": "test",
                "note": "This is a test image. WAN2.1 models are not loaded."
            }
        }
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# RunPod serverless mode
if __name__ == "__main__":
    print("WAN2.1 T2I Test Mode Worker")
    print("=" * 50)
    print("Running in test mode - actual models not loaded")
    print("Starting RunPod server...")
    
    runpod.serverless.start({"handler": handler})