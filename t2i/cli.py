#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Host-side CLI tool for WAN2.1 T2I (Text-to-Image) static image generation.
This script sends HTTP requests to the local RunPod API server.
"""
import os
import json
import argparse
import requests
import time

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate static image using WAN2.1 T2I model via API")
    parser.add_argument("-p", "--positive-prompt", help="Positive prompt describing desired image")
    parser.add_argument("-n", "--negative-prompt", help="Negative prompt describing undesired content")
    parser.add_argument("-w", "--width", type=int, help="Output image width")
    parser.add_argument("--height", type=int, help="Output image height")
    parser.add_argument("-s", "--steps", type=int, help="Number of inference steps")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument("--cfg", type=float, help="CFG guidance scale")
    parser.add_argument("--api-url", default="http://localhost:8083", help="API server URL")
    parser.add_argument("--sync", action="store_true", help="Use synchronous API endpoint")
    
    args = parser.parse_args()
    
    # Build request payload
    payload = {
        "input": {
            "positive_prompt": args.positive_prompt or os.getenv("POSITIVE_PROMPT", "A beautiful mountain landscape"),
            "negative_prompt": args.negative_prompt or os.getenv("NEGATIVE_PROMPT", "blurry, low quality"),
            "width": args.width or int(os.getenv("WIDTH", "576")),
            "height": args.height or int(os.getenv("HEIGHT", "576")),
            "length": 1,  # Always 1 for static images
            "steps": args.steps or int(os.getenv("STEPS", "20")),
            "cfg": args.cfg or float(os.getenv("CFG", "7.0")),
            "seed": args.seed or int(os.getenv("SEED", "0"))
        }
    }
    
    print("🎨 Starting WAN2.1 T2I Static Image Generation")
    print("=" * 50)
    print(f"API Server: {args.api_url}")
    print(f"Prompt: {payload['input']['positive_prompt']}")
    print(f"Resolution: {payload['input']['width']}x{payload['input']['height']}")
    print(f"Steps: {payload['input']['steps']}")
    print(f"CFG: {payload['input']['cfg']}")
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
                time.sleep(2)
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
        
        print("\n✨ Generation Complete!")
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