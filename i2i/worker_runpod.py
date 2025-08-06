import os, json, requests, random, time, runpod
from PIL import Image
import numpy as np

print("Starting worker_runpod_debug.py...")

# Simple test handler that generates colored rectangles
def generate(input):
    start_time = time.time()
    
    try:
        values = input["input"]
        
        # Get parameters
        positive_prompt = values.get('positive_prompt', 'test')
        width = values.get('width', 576)
        height = values.get('height', 576)
        seed = values.get('seed', 42)
        
        print(f"Generating test image: {width}x{height}, prompt: {positive_prompt}")
        
        # Create a gradient based on seed
        np.random.seed(seed)
        r = np.random.randint(50, 200)
        g = np.random.randint(50, 200)
        b = np.random.randint(50, 200)
        
        # Create gradient image
        img = np.zeros((height, width, 3), dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                img[y, x] = [
                    min(255, r + (x * 50 // width)),
                    min(255, g + (y * 50 // height)),
                    b
                ]
        
        # Add text overlay with prompt info
        from PIL import ImageDraw, ImageFont
        pil_img = Image.fromarray(img)
        draw = ImageDraw.Draw(pil_img)
        try:
            # Try to use a basic font
            font = ImageFont.load_default()
            text = f"Seed: {seed}\n{positive_prompt[:30]}..."
            draw.text((10, 10), text, fill=(255, 255, 255), font=font)
        except:
            pass
        
        # Save
        os.makedirs("/content/ComfyUI/output", exist_ok=True)
        result_path = f"/content/ComfyUI/output/wan2.2-debug-{seed}.png"
        pil_img.save(result_path)
        
        print(f"Test image saved to: {result_path}")
        
        execution_time = round(time.time() - start_time, 2)
        
        return {
            "jobId": f"debug-{seed}",
            "result": result_path,
            "status": "DONE",
            "message": "Debug test image generated",
            "execution_time": execution_time
        }
        
    except Exception as e:
        print(f"Error in debug generate: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "jobId": "debug-error",
            "result": f"FAILED: {str(e)}",
            "status": "FAILED",
            "execution_time": round(time.time() - start_time, 2)
        }

print("Starting RunPod server...")
runpod.serverless.start({"handler": generate})