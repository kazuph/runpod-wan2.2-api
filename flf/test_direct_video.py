#!/usr/bin/env python3
"""
Test FLF with direct video output (no ffmpeg needed)
"""

import json
import requests
import time
import os
import random

COMFYUI_URL = "http://localhost:8188"

def upload_image(path):
    """Upload image to ComfyUI"""
    with open(path, 'rb') as f:
        files = {"image": (os.path.basename(path), f, "image/jpeg")}
        response = requests.post(f"{COMFYUI_URL}/upload/image", files=files)
        return response.json().get("name")

print("🎬 FLF Direct Video Output Test")
print("="*50)

# Upload images
img1 = upload_image("/home/kazuph/runpod-wan2.2-api/rapid-i2v/input/girl1.jpg")
img2 = upload_image("/home/kazuph/runpod-wan2.2-api/rapid-i2v/input/girl2.jpg")

seed = random.randint(1000, 9999)

# Workflow with SaveVideo node instead of SaveImage
workflow = {
    "1": {
        "inputs": {
            "ckpt_name": "wan2.2-i2v-rapid-aio.safetensors"
        },
        "class_type": "CheckpointLoaderSimple"
    },
    "2": {
        "inputs": {
            "image": img1,
            "upload": "image"
        },
        "class_type": "LoadImage"
    },
    "3": {
        "inputs": {
            "image": img2,
            "upload": "image"
        },
        "class_type": "LoadImage"
    },
    "4": {
        "inputs": {
            "text": "smooth morphing transition between two faces over 3 seconds",
            "clip": ["1", 1]
        },
        "class_type": "CLIPTextEncode"
    },
    "5": {
        "inputs": {
            "text": "static, blurry, distortion",
            "clip": ["1", 1]
        },
        "class_type": "CLIPTextEncode"
    },
    "6": {
        "inputs": {
            "positive": ["4", 0],
            "negative": ["5", 0],
            "vae": ["1", 2],
            "start_image": ["2", 0],
            "end_image": ["3", 0],
            "width": 512,
            "height": 512,
            "length": 49,  # 2 seconds
            "batch_size": 1
        },
        "class_type": "WanFirstLastFrameToVideo"
    },
    "7": {
        "inputs": {
            "model": ["1", 0],
            "positive": ["6", 0],
            "negative": ["6", 1],
            "latent_image": ["6", 2],
            "seed": seed,
            "steps": 4,
            "cfg": 1.0,
            "sampler_name": "lcm",
            "scheduler": "beta",
            "denoise": 1.0
        },
        "class_type": "KSampler"
    },
    "8": {
        "inputs": {
            "samples": ["7", 0],
            "vae": ["1", 2]
        },
        "class_type": "VAEDecode"
    },
    "9": {
        "inputs": {
            "images": ["8", 0],
            "fps": 24.0,
            "codec": "h264",
            "quality": 19,
            "filename_prefix": f"flf_direct_{seed}"
        },
        "class_type": "SaveVideo"
    }
}

print(f"🚀 Sending workflow with SaveVideo node (Seed: {seed})")
response = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
result = response.json()

prompt_id = result.get("prompt_id")
if not prompt_id:
    print(f"❌ Failed: {result}")
    # Check if SaveVideo is not available
    if "SaveVideo" in str(result):
        print("\n⚠️  SaveVideo node not found. Checking available video nodes...")
        
        # Get available nodes
        nodes_response = requests.get(f"{COMFYUI_URL}/object_info")
        nodes = nodes_response.json()
        video_nodes = [k for k in nodes.keys() if 'video' in k.lower()]
        print(f"Available video nodes: {', '.join(video_nodes[:10])}")
    exit(1)

print(f"📋 Prompt ID: {prompt_id}")
print("⏳ Processing...")

# Wait for completion
start_time = time.time()
for i in range(60):
    history = requests.get(f"{COMFYUI_URL}/history/{prompt_id}").json()
    
    if prompt_id in history:
        if "outputs" in history[prompt_id]:
            elapsed = time.time() - start_time
            print(f"\n✅ Complete in {elapsed:.1f}s!")
            
            outputs = history[prompt_id]["outputs"]
            for node_id, output in outputs.items():
                if "gifs" in output:  # Video outputs are often in 'gifs' key
                    for video in output["gifs"]:
                        print(f"🎥 Direct video output: {video['filename']}")
                        print(f"   Format: {video.get('format', 'mp4')}")
                elif "videos" in output:
                    for video in output["videos"]:
                        print(f"🎥 Direct video output: {video['filename']}")
                elif "images" in output:
                    # Still outputting images
                    frame_count = len(output["images"])
                    print(f"⚠️  Still outputting {frame_count} frames instead of video")
                    print("   Need to configure video output properly in ComfyUI")
            exit(0)
        
        if "status" in history[prompt_id]:
            status = history[prompt_id]["status"]
            if status.get("status_str") == "error":
                print(f"\n❌ Error: {status}")
                exit(1)
    
    print(".", end="", flush=True)
    time.sleep(2)

print("\n❌ Timeout")
exit(1)