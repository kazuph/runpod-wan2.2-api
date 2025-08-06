import os, json, requests, random, time, runpod
from PIL import Image
import numpy as np

def generate(input):
    start_time = time.time()
    
    try:
        values = input["input"]
        
        # Get parameters
        positive_prompt = values.get('positive_prompt', 'A beautiful landscape')
        negative_prompt = values.get('negative_prompt', '')
        width = values.get('width', 576)
        height = values.get('height', 576)
        seed = values.get('seed', 0)
        if seed == 0:
            random.seed(int(time.time()))
            seed = random.randint(0, 18446744073709551615)
        
        print(f"Generating test image with prompt: {positive_prompt}")
        print(f"Resolution: {width}x{height}, Seed: {seed}")
        
        # Create a test gradient image
        img_array = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Create gradient based on seed
        r_base = (seed % 256)
        g_base = ((seed // 256) % 256)
        b_base = ((seed // 65536) % 256)
        
        for y in range(height):
            for x in range(width):
                img_array[y, x] = [
                    min(255, r_base + (x * 100 // width)),
                    min(255, g_base + (y * 100 // height)),
                    b_base
                ]
        
        # Save image
        os.makedirs("/content/ComfyUI/output", exist_ok=True)
        result_path = f"/content/ComfyUI/output/wan2.1-t2i-test-{seed}.png"
        
        img = Image.fromarray(img_array, 'RGB')
        img.save(result_path, 'PNG', optimize=True)
        
        print(f"Test image saved to: {result_path}")
        
        job_id = values.get('job_id', f'job-{seed}')
        execution_time = round(time.time() - start_time, 2)
        
        return {
            "jobId": job_id,
            "result": result_path,
            "status": "DONE",
            "message": "WAN2.1 T2I test image generated (gradient test mode)",
            "execution_time": execution_time
        }
        
    except Exception as e:
        print(f"Error in generate: {str(e)}")
        import traceback
        traceback.print_exc()
        
        job_id = values.get('job_id', 'error-job') if 'values' in locals() else 'error-job'
        execution_time = round(time.time() - start_time, 2)
        
        return {
            "jobId": job_id,
            "result": f"FAILED: {str(e)}",
            "status": "FAILED",
            "execution_time": execution_time
        }

print("Starting RunPod test server on port 8083...")
runpod.serverless.start({"handler": generate})