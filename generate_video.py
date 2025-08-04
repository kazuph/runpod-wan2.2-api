#!/usr/bin/env python3
"""
Generate video using environment variables instead of JSON file.
This script reads parameters from environment variables and calls the worker directly.
"""
import os
import json
from worker_runpod import generate

def main():
    # Read parameters from environment variables
    input_data = {
        "input": {
            "input_image": os.getenv("INPUT_IMAGE", "https://s3.tost.ai/input/a2784ea5-0d9b-41e0-8eb2-69be58261074.png"),
            "positive_prompt": os.getenv("POSITIVE_PROMPT", "A beautiful scene with dynamic movement"),
            "negative_prompt": os.getenv("NEGATIVE_PROMPT", "static, blurry, low quality"),
            "crop": os.getenv("CROP", "center"),
            "width": int(os.getenv("WIDTH", "720")),
            "height": int(os.getenv("HEIGHT", "480")),
            "length": int(os.getenv("LENGTH", "53")),
            "batch_size": int(os.getenv("BATCH_SIZE", "1")),
            "shift": float(os.getenv("SHIFT", "8.0")),
            "cfg": float(os.getenv("CFG", "1.0")),
            "sampler_name": os.getenv("SAMPLER_NAME", "lcm"),
            "scheduler": os.getenv("SCHEDULER", "beta"),
            "steps": int(os.getenv("STEPS", "4")),
            "seed": int(os.getenv("SEED", "42")),
            "fps": int(os.getenv("FPS", "24")),
            "job_id": os.getenv("JOB_ID", f"env-job-{os.getenv('SEED', '42')}")
        }
    }
    
    print("🎬 Starting WAN2.2 I2V Generation")
    print("=" * 50)
    print(f"Input Image: {input_data['input']['input_image']}")
    print(f"Prompt: {input_data['input']['positive_prompt']}")
    print(f"Resolution: {input_data['input']['width']}x{input_data['input']['height']}")  
    print(f"Steps: {input_data['input']['steps']}")
    print(f"Seed: {input_data['input']['seed']}")
    print("=" * 50)
    
    # Generate video
    result = generate(input_data)
    
    print("\n🎉 Generation Complete!")
    print(f"Status: {result['status']}")
    print(f"Output: {result['result']}")
    if 'message' in result:
        print(f"Message: {result['message']}")

if __name__ == "__main__":
    main()