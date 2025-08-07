#!/usr/bin/env python3
"""
Quick FLF test with GGUF model
"""

import json
import requests
import time
import os

COMFYUI_URL = "http://localhost:8188"

def upload_image(path):
    """Upload image to ComfyUI"""
    with open(path, 'rb') as f:
        files = {"image": (os.path.basename(path), f, "image/jpeg")}
        response = requests.post(f"{COMFYUI_URL}/upload/image", files=files)
        return response.json().get("name")

print("🎬 Quick FLF Test with GGUF Model")
print("="*50)

# Check ComfyUI
try:
    response = requests.get(f"{COMFYUI_URL}/system_stats")
    print("✅ ComfyUI is running")
except:
    print("❌ ComfyUI not accessible")
    exit(1)

# Upload images
print("📤 Uploading images...")
start_img = upload_image("/home/kazuph/runpod-wan2.2-api/rapid-i2v/input/girl1.jpg")
end_img = upload_image("/home/kazuph/runpod-wan2.2-api/rapid-i2v/input/girl2.jpg")

# Simple workflow using existing models
workflow = {
    "1": {
        "inputs": {
            "ckpt_name": "wan2.2-i2v-rapid-aio.safetensors"
        },
        "class_type": "CheckpointLoaderSimple"
    },
    "2": {
        "inputs": {
            "image": start_img,
            "upload": "image"
        },
        "class_type": "LoadImage"
    },
    "3": {
        "inputs": {
            "image": end_img,
            "upload": "image"
        },
        "class_type": "LoadImage"
    },
    "4": {
        "inputs": {
            "text": "smooth transition between two faces",
            "clip": ["1", 1]
        },
        "class_type": "CLIPTextEncode"
    },
    "5": {
        "inputs": {
            "text": "static, blurry",
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
            "length": 25,
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
            "seed": 42,
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
            "filename_prefix": "flf_test"
        },
        "class_type": "SaveImage"
    }
}

print("🚀 Queueing workflow...")
response = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
result = response.json()

prompt_id = result.get("prompt_id")
if not prompt_id:
    print(f"❌ Failed: {result}")
    exit(1)

print(f"ID: {prompt_id}")
print("⏳ Processing...")

# Wait for completion
start_time = time.time()
while time.time() - start_time < 60:
    history = requests.get(f"{COMFYUI_URL}/history/{prompt_id}").json()
    
    if prompt_id in history:
        if "outputs" in history[prompt_id]:
            print(f"\n✅ Complete in {time.time()-start_time:.1f}s!")
            
            outputs = history[prompt_id]["outputs"]
            for node_id, output in outputs.items():
                if "images" in output:
                    for img in output["images"]:
                        print(f"📹 Output: {img['filename']}")
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