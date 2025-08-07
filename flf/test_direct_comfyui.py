#!/usr/bin/env python3
"""
Test FLF directly with existing ComfyUI instance
"""

import json
import requests
import time
import os
import base64
from pathlib import Path

COMFYUI_URL = "http://localhost:8188"

def queue_prompt(prompt):
    """Queue a prompt to ComfyUI"""
    p = {"prompt": prompt}
    response = requests.post(f"{COMFYUI_URL}/prompt", json=p)
    return response.json()

def get_history(prompt_id):
    """Get history for a prompt"""
    response = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
    return response.json()

def upload_image(image_path):
    """Upload an image to ComfyUI"""
    with open(image_path, 'rb') as f:
        files = {"image": (os.path.basename(image_path), f, "image/png")}
        data = {"overwrite": "true"}
        response = requests.post(f"{COMFYUI_URL}/upload/image", files=files, data=data)
        return response.json()

def test_flf():
    """Test FLF workflow"""
    
    print("🧪 Testing FLF with existing ComfyUI...")
    
    # Check if ComfyUI is running
    try:
        response = requests.get(f"{COMFYUI_URL}/system_stats")
        print(f"✅ ComfyUI is running")
    except:
        print("❌ ComfyUI not accessible")
        return False
    
    # Upload test images
    start_image_path = "/home/kazuph/runpod-wan2.2-api/rapid-i2v/input/girl1.jpg"
    end_image_path = "/home/kazuph/runpod-wan2.2-api/rapid-i2v/input/girl2.jpg"
    
    print(f"Uploading start image: {start_image_path}")
    start_upload = upload_image(start_image_path)
    start_image_name = start_upload.get("name", "girl1.jpg")
    print(f"  Uploaded as: {start_image_name}")
    
    print(f"Uploading end image: {end_image_path}")
    end_upload = upload_image(end_image_path)
    end_image_name = end_upload.get("name", "girl2.jpg")
    print(f"  Uploaded as: {end_image_name}")
    
    # Create a simple I2V workflow first (since we know I2V works)
    # We'll adapt it for FLF testing
    workflow = {
        # Load image nodes
        "1": {
            "inputs": {
                "image": start_image_name,
                "upload": "image"
            },
            "class_type": "LoadImage"
        },
        "2": {
            "inputs": {
                "image": end_image_name,
                "upload": "image"
            },
            "class_type": "LoadImage"
        },
        
        # Load models (using rapid-i2v model as fallback)
        "3": {
            "inputs": {
                "ckpt_name": "wan2.2-i2v-rapid-aio.safetensors"
            },
            "class_type": "CheckpointLoaderSimple"
        },
        
        # Text encoding
        "4": {
            "inputs": {
                "text": "smooth morphing transition between two faces, gradual transformation",
                "clip": ["3", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "5": {
            "inputs": {
                "text": "static, blurry, distortion, abrupt change",
                "clip": ["3", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        
        # Image to latent
        "6": {
            "inputs": {
                "pixels": ["1", 0],
                "vae": ["3", 2]
            },
            "class_type": "VAEEncode"
        },
        
        # KSampler
        "7": {
            "inputs": {
                "seed": 42,
                "steps": 4,
                "cfg": 1.0,
                "sampler_name": "lcm",
                "scheduler": "beta",
                "denoise": 0.95,
                "model": ["3", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["6", 0]
            },
            "class_type": "KSampler"
        },
        
        # Decode
        "8": {
            "inputs": {
                "samples": ["7", 0],
                "vae": ["3", 2]
            },
            "class_type": "VAEDecode"
        },
        
        # Save
        "9": {
            "inputs": {
                "images": ["8", 0],
                "filename_prefix": "flf_test"
            },
            "class_type": "SaveImage"
        }
    }
    
    # Queue the workflow
    print("\nQueuing workflow...")
    result = queue_prompt(workflow)
    prompt_id = result.get('prompt_id')
    
    if not prompt_id:
        print(f"❌ Failed to queue workflow: {result}")
        return False
    
    print(f"Prompt ID: {prompt_id}")
    print("Waiting for completion...")
    
    # Wait for completion
    max_wait = 60
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        history = get_history(prompt_id)
        
        if prompt_id in history:
            status = history[prompt_id].get('status', {})
            
            if 'status_str' in status:
                if status['status_str'] == 'success':
                    print("✅ Workflow completed successfully!")
                    
                    outputs = history[prompt_id].get('outputs', {})
                    for node_id, output in outputs.items():
                        if 'images' in output:
                            for img in output['images']:
                                print(f"  Output image: {img['filename']}")
                    
                    return True
                elif status['status_str'] == 'error':
                    print(f"❌ Workflow failed: {status}")
                    return False
        
        time.sleep(2)
        print(".", end="", flush=True)
    
    print("\n❌ Workflow timeout")
    return False

if __name__ == "__main__":
    success = test_flf()
    exit(0 if success else 1)