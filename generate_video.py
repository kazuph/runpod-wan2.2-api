#!/usr/bin/env python3
"""
Generate video using command line arguments or environment variables.
This script reads parameters from CLI args (priority) or environment variables and calls the worker directly.
"""
import os
import json
import argparse
from worker_runpod import generate

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate video using WAN2.2 I2V model")
    parser.add_argument("-i", "--input-image", help="Input image path or URL")
    parser.add_argument("-p", "--positive-prompt", help="Positive prompt describing desired content")
    parser.add_argument("-n", "--negative-prompt", help="Negative prompt describing undesired content")
    parser.add_argument("--crop", choices=["center", "top", "bottom"], help="Image cropping method")
    parser.add_argument("-w", "--width", type=int, help="Video width")
    parser.add_argument("--height", type=int, help="Video height")
    parser.add_argument("-l", "--length", type=int, help="Video length in frames")
    parser.add_argument("-s", "--steps", type=int, help="Number of inference steps")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument("--fps", type=int, help="Frames per second")
    parser.add_argument("--cfg", type=float, help="CFG guidance scale")
    parser.add_argument("--shift", type=float, help="Shift parameter")
    parser.add_argument("--sampler", help="Sampler name")
    parser.add_argument("--scheduler", help="Scheduler name")
    parser.add_argument("--batch-size", type=int, help="Batch size")
    parser.add_argument("--job-id", help="Job ID for tracking")
    
    args = parser.parse_args()
    
    # Read parameters from CLI args (priority) or environment variables (fallback)
    input_data = {
        "input": {
            "input_image": args.input_image or os.getenv("INPUT_IMAGE", "https://s3.tost.ai/input/a2784ea5-0d9b-41e0-8eb2-69be58261074.png"),
            "positive_prompt": args.positive_prompt or os.getenv("POSITIVE_PROMPT", "A beautiful scene with dynamic movement"),
            "negative_prompt": args.negative_prompt or os.getenv("NEGATIVE_PROMPT", "static, blurry, low quality"),
            "crop": args.crop or os.getenv("CROP", "center"),
            "width": args.width or int(os.getenv("WIDTH", "720")),
            "height": args.height or int(os.getenv("HEIGHT", "480")),
            "length": args.length or int(os.getenv("LENGTH", "53")),
            "batch_size": args.batch_size or int(os.getenv("BATCH_SIZE", "1")),
            "shift": args.shift or float(os.getenv("SHIFT", "8.0")),
            "cfg": args.cfg or float(os.getenv("CFG", "1.0")),
            "sampler_name": args.sampler or os.getenv("SAMPLER_NAME", "lcm"),
            "scheduler": args.scheduler or os.getenv("SCHEDULER", "beta"),
            "steps": args.steps or int(os.getenv("STEPS", "4")),
            "seed": args.seed or int(os.getenv("SEED", "42")),
            "fps": args.fps or int(os.getenv("FPS", "24")),
            "job_id": args.job_id or os.getenv("JOB_ID", f"cli-job-{args.seed or os.getenv('SEED', '42')}")
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