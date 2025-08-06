#!/usr/bin/env python3
"""
Host-side CLI tool for WAN2.2 I2V video generation.
This script sends HTTP requests to the local RunPod API server.
"""
import os
import json
import argparse
import requests
import time
from PIL import Image
from urllib.parse import urlparse

def get_image_dimensions(image_path):
    """Get dimensions of an image from URL or local path."""
    try:
        if image_path.startswith(('http://', 'https://')):
            # Download image temporarily to get dimensions
            response = requests.get(image_path, stream=True)
            response.raise_for_status()
            img = Image.open(response.raw)
        else:
            # Local file
            if not os.path.isabs(image_path):
                # Check in input directory first
                input_path = os.path.join("input", image_path)
                if os.path.exists(input_path):
                    image_path = input_path
            img = Image.open(image_path)
        
        return img.width, img.height
    except Exception as e:
        print(f"Warning: Could not read image dimensions: {e}")
        return None, None

def calculate_optimal_resolution(orig_width, orig_height, max_pixels=576*576):
    """
    Calculate optimal resolution maintaining aspect ratio while staying within VRAM limits.
    Based on CLAUDE.md GPU memory safe resolutions for RTX 3090 24GB.
    """
    aspect_ratio = orig_width / orig_height
    
    # Define safe resolution limits based on aspect ratio
    if aspect_ratio > 1.5:  # Wide/horizontal video
        # Maximum safe: 720x480
        target_width = 720
        target_height = 480
    elif aspect_ratio < 0.67:  # Tall/vertical video  
        # Maximum safe: 480x720
        target_width = 480
        target_height = 720
    else:  # Near square or moderate aspect ratio
        # Maximum safe: 576x576 for reliability
        if orig_width * orig_height > max_pixels:
            # Scale down to fit within max_pixels
            scale = (max_pixels / (orig_width * orig_height)) ** 0.5
            target_width = int(orig_width * scale)
            target_height = int(orig_height * scale)
        else:
            target_width = orig_width
            target_height = orig_height
    
    # Ensure dimensions are multiples of 8 (required by model)
    target_width = (target_width // 8) * 8
    target_height = (target_height // 8) * 8
    
    # Final safety check - ensure we don't exceed 720 in any dimension
    if target_width > 720:
        scale = 720 / target_width
        target_width = 720
        target_height = int(target_height * scale)
        target_height = (target_height // 8) * 8
    
    if target_height > 720:
        scale = 720 / target_height
        target_height = 720
        target_width = int(target_width * scale)
        target_width = (target_width // 8) * 8
    
    return target_width, target_height

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate video using WAN2.2 I2V model via API")
    parser.add_argument("-i", "--input-image", help="Input image path or URL")
    parser.add_argument("-p", "--positive-prompt", help="Positive prompt describing desired content")
    parser.add_argument("-n", "--negative-prompt", help="Negative prompt describing undesired content")
    parser.add_argument("--crop", choices=["center", "top", "bottom"], help="Image cropping method")
    parser.add_argument("-w", "--width", type=int, help="Video width (auto-detected if not specified)")
    parser.add_argument("--height", type=int, help="Video height (auto-detected if not specified)")
    parser.add_argument("-l", "--length", type=int, help="Video length in frames")
    parser.add_argument("-s", "--steps", type=int, help="Number of inference steps")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument("--fps", type=int, help="Frames per second")
    parser.add_argument("--cfg", type=float, help="CFG guidance scale")
    parser.add_argument("--shift", type=float, help="Shift parameter")
    parser.add_argument("--sampler", help="Sampler name")
    parser.add_argument("--scheduler", help="Scheduler name")
    parser.add_argument("--batch-size", type=int, help="Batch size")
    parser.add_argument("--api-url", default="http://localhost:8080", help="API server URL")
    parser.add_argument("--sync", action="store_true", help="Use synchronous API endpoint")
    parser.add_argument("--auto-resize", action="store_true", default=True, help="Auto-detect and maintain aspect ratio (default: True)")
    parser.add_argument("--no-auto-resize", dest="auto_resize", action="store_false", help="Disable auto-resize")
    
    args = parser.parse_args()
    
    # Get input image
    input_image = args.input_image or os.getenv("INPUT_IMAGE", "https://s3.tost.ai/input/a2784ea5-0d9b-41e0-8eb2-69be58261074.png")
    
    # Auto-detect dimensions if not specified and auto-resize is enabled
    if args.auto_resize and (args.width is None or args.height is None):
        orig_width, orig_height = get_image_dimensions(input_image)
        if orig_width and orig_height:
            auto_width, auto_height = calculate_optimal_resolution(orig_width, orig_height)
            if args.width is None:
                args.width = auto_width
            if args.height is None:
                args.height = auto_height
            print(f"📐 Auto-detected resolution: {orig_width}x{orig_height} → {args.width}x{args.height} (aspect ratio preserved)")
    
    # Build request payload
    payload = {
        "input": {
            "input_image": input_image,
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
            "fps": args.fps or int(os.getenv("FPS", "24"))
        }
    }
    
    print("🎬 Starting WAN2.2 I2V Generation")
    print("=" * 50)
    print(f"API Server: {args.api_url}")
    print(f"Input Image: {payload['input']['input_image']}")
    print(f"Prompt: {payload['input']['positive_prompt']}")
    print(f"Resolution: {payload['input']['width']}x{payload['input']['height']}")  
    print(f"Steps: {payload['input']['steps']}")
    print(f"Seed: {payload['input']['seed']}")
    print("=" * 50)
    
    try:
        # Start timing
        start_time = time.time()
        
        if args.sync:
            # Use synchronous endpoint
            print("Using synchronous API endpoint...")
            response = requests.post(f"{args.api_url}/runsync", json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
        else:
            # Use asynchronous endpoint
            print("Submitting job to API...")
            response = requests.post(f"{args.api_url}/run", json=payload)
            response.raise_for_status()
            job_data = response.json()
            job_id = job_data.get("id")
            
            print(f"Job ID: {job_id}")
            print("Polling for results...")
            
            # Poll for results
            while True:
                time.sleep(5)
                status_response = requests.get(f"{args.api_url}/status/{job_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get("status")
                    
                    if status == "COMPLETED":
                        result = status_data.get("output", {})
                        break
                    elif status == "FAILED":
                        result = status_data.get("output", {"status": "FAILED", "message": "Job failed"})
                        break
                    else:
                        print(f"Status: {status}...")
                else:
                    print(f"Status check failed: {status_response.status_code}")
        
        # Calculate total time
        total_time = time.time() - start_time
        
        print("\n🎉 Generation Complete!")
        print(f"Status: {result.get('status', 'UNKNOWN')}")
        print(f"Output: {result.get('result', 'N/A')}")
        print(f"API Execution Time: {result.get('execution_time', 'N/A')} seconds")
        print(f"Total Time (including network): {total_time:.2f} seconds")
        if 'message' in result:
            print(f"Message: {result['message']}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ API Error: {str(e)}")
        return 1
    except KeyboardInterrupt:
        print("\n⚠️ Generation cancelled by user")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())