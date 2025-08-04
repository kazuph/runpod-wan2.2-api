#!/usr/bin/env python3
"""
Generate FLF (First-Last Frame) video using command line arguments or environment variables.
This script reads parameters from CLI args (priority) or environment variables and calls the FLF worker directly.
"""
import os
import json
import argparse
from worker_runpod import generate

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate FLF video using WAN2.2 I2V model")
    parser.add_argument("-i", "--start-image", help="Start image path or URL")
    parser.add_argument("-e", "--end-image", help="End image path or URL")
    parser.add_argument("-p", "--positive-prompt", help="Positive prompt describing desired content")
    parser.add_argument("-n", "--negative-prompt", help="Negative prompt describing undesired content")
    parser.add_argument("-w", "--width", type=int, help="Video width")
    parser.add_argument("--height", type=int, help="Video height")
    parser.add_argument("-l", "--length", type=int, help="Video length in frames")
    parser.add_argument("-s", "--steps", type=int, help="Number of inference steps")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument("--fps", type=int, help="Frames per second")
    parser.add_argument("--cfg", type=float, help="CFG guidance scale")
    parser.add_argument("--shift", type=float, help="Shift parameter")
    parser.add_argument("--batch-size", type=int, help="Batch size")
    parser.add_argument("--job-id", help="Job ID for tracking")
    
    args = parser.parse_args()
    
    # Read parameters from CLI args (priority) or environment variables (fallback)
    input_data = {
        "input": {
            "start_image": args.start_image or os.getenv("START_IMAGE", "start.jpg"),
            "end_image": args.end_image or os.getenv("END_IMAGE", "end.jpg"),
            "positive_prompt": args.positive_prompt or os.getenv("POSITIVE_PROMPT", "smooth transition animation between frames"),
            "negative_prompt": args.negative_prompt or os.getenv("NEGATIVE_PROMPT", "static, blurry, low quality, mouth opening, talking"),
            "width": args.width or int(os.getenv("WIDTH", "720")),
            "height": args.height or int(os.getenv("HEIGHT", "1280")),
            "length": args.length or int(os.getenv("LENGTH", "81")),
            "batch_size": args.batch_size or int(os.getenv("BATCH_SIZE", "1")),
            "shift": args.shift or float(os.getenv("SHIFT", "8.0")),
            "cfg": args.cfg or float(os.getenv("CFG", "4.0")),
            "steps": args.steps or int(os.getenv("STEPS", "20")),
            "seed": args.seed or int(os.getenv("SEED", "42")),
            "fps": args.fps or int(os.getenv("FPS", "24")),
            "job_id": args.job_id or os.getenv("JOB_ID", f"flf-job-{args.seed or os.getenv('SEED', '42')}")
        }
    }
    
    print("🎬 Starting WAN2.2 FLF (First-Last Frame) Generation")
    print("=" * 50)
    print(f"Start Image: {input_data['input']['start_image']}")
    print(f"End Image: {input_data['input']['end_image']}")
    print(f"Prompt: {input_data['input']['positive_prompt']}")
    print(f"Resolution: {input_data['input']['width']}x{input_data['input']['height']}")  
    print(f"Length: {input_data['input']['length']} frames")
    print(f"Steps: {input_data['input']['steps']}")
    print(f"Seed: {input_data['input']['seed']}")
    print("=" * 50)
    
    # Generate FLF video
    result = generate(input_data)
    
    print("\n🎉 FLF Generation Complete!")
    print(f"Status: {result['status']}")
    print(f"Output: {result['result']}")
    if 'message' in result:
        print(f"Message: {result['message']}")

if __name__ == "__main__":
    main()