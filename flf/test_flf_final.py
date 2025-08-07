#!/usr/bin/env python3
"""
Final FLF test with GGUF model
Tests the complete FLF pipeline with Q3_K_M quantized model
"""

import json
import requests
import time
import os
import sys
from pathlib import Path

COMFYUI_URL = "http://localhost:8188"

def wait_for_model_download():
    """Wait for GGUF model to finish downloading"""
    model_path = Path("/home/kazuph/runpod-wan2.2-api/flf/models/unet_gguf/Wan2.1-FLF2V-14B-720P-Q3_K_M.gguf")
    expected_size_gb = 8.59  # Q3_K_M is 8.59 GB
    
    print(f"⏳ Waiting for model download to complete...")
    print(f"   Expected size: {expected_size_gb} GB")
    
    while True:
        if model_path.exists():
            current_size_gb = model_path.stat().st_size / (1024**3)
            print(f"   Current size: {current_size_gb:.2f} GB", end='\r')
            
            if current_size_gb >= expected_size_gb * 0.99:  # 99% complete
                print(f"\n✅ Model download complete: {current_size_gb:.2f} GB")
                return True
        
        time.sleep(5)

def test_flf_pipeline():
    """Test the complete FLF pipeline"""
    
    print("\n" + "="*60)
    print("🎬 WAN2.1 FLF GGUF Pipeline Test")
    print("="*60)
    
    # Wait for model to be ready
    if not wait_for_model_download():
        print("❌ Model download failed")
        return False
    
    # Check ComfyUI
    try:
        response = requests.get(f"{COMFYUI_URL}/system_stats")
        print("✅ ComfyUI server is running")
    except:
        print("❌ ComfyUI server not accessible")
        return False
    
    # Upload test images
    print("\n📤 Uploading test images...")
    
    def upload_image(path):
        with open(path, 'rb') as f:
            files = {"image": (os.path.basename(path), f, "image/jpeg")}
            response = requests.post(f"{COMFYUI_URL}/upload/image", files=files)
            return response.json().get("name")
    
    start_img = upload_image("/home/kazuph/runpod-wan2.2-api/rapid-i2v/input/girl1.jpg")
    end_img = upload_image("/home/kazuph/runpod-wan2.2-api/rapid-i2v/input/girl2.jpg")
    
    print(f"  Start: {start_img}")
    print(f"  End: {end_img}")
    
    # Create workflow
    workflow = {
        "1": {
            "inputs": {
                "unet_name": "Wan2.1-FLF2V-14B-720P-Q3_K_M.gguf",
                "model_path": "/home/kazuph/runpod-wan2.2-api/flf/models/unet_gguf"
            },
            "class_type": "UNETLoader",
            "_meta": {"title": "Load UNET (GGUF)"}
        },
        "2": {
            "inputs": {
                "clip_name": "t5xxl_fp8_e4m3fn.safetensors",
                "type": "sd3"
            },
            "class_type": "CLIPLoader",
            "_meta": {"title": "Load CLIP"}
        },
        "3": {
            "inputs": {
                "vae_name": "Wan2.1_VAE.pth"
            },
            "class_type": "VAELoader",
            "_meta": {"title": "Load VAE"}
        },
        "4": {
            "inputs": {
                "image": start_img,
                "upload": "image"
            },
            "class_type": "LoadImage",
            "_meta": {"title": "Start Image"}
        },
        "5": {
            "inputs": {
                "image": end_img,
                "upload": "image"
            },
            "class_type": "LoadImage",
            "_meta": {"title": "End Image"}
        },
        "6": {
            "inputs": {
                "text": "smooth morphing transition between two beautiful faces, gradual transformation",
                "clip": ["2", 0]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "Positive"}
        },
        "7": {
            "inputs": {
                "text": "static, blurry, distortion, artifacts",
                "clip": ["2", 0]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "Negative"}
        },
        "8": {
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "vae": ["3", 0],
                "start_image": ["4", 0],
                "end_image": ["5", 0],
                "width": 512,
                "height": 512,
                "length": 25,  # 1 second at 24fps
                "batch_size": 1
            },
            "class_type": "WanFirstLastFrameToVideo",
            "_meta": {"title": "FLF Generator"}
        },
        "9": {
            "inputs": {
                "model": ["1", 0],
                "positive": ["8", 0],
                "negative": ["8", 1],
                "latent_image": ["8", 2],
                "seed": 42,
                "steps": 15,
                "cfg": 3.5,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0
            },
            "class_type": "KSampler",
            "_meta": {"title": "Sample"}
        },
        "10": {
            "inputs": {
                "samples": ["9", 0],
                "vae": ["3", 0]
            },
            "class_type": "VAEDecode",
            "_meta": {"title": "Decode"}
        },
        "11": {
            "inputs": {
                "images": ["10", 0],
                "filename_prefix": "flf_gguf_test"
            },
            "class_type": "SaveImage",
            "_meta": {"title": "Save"}
        }
    }
    
    # Queue workflow
    print("\n🚀 Queueing FLF workflow...")
    print("  Model: Q3_K_M (8.59 GB)")
    print("  Resolution: 512x512")
    print("  Frames: 25 (1 second)")
    
    response = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
    result = response.json()
    
    prompt_id = result.get("prompt_id")
    if not prompt_id:
        print(f"❌ Failed to queue: {result}")
        return False
    
    print(f"  ID: {prompt_id}")
    
    # Wait for completion
    print("\n⏳ Processing...")
    start_time = time.time()
    
    while time.time() - start_time < 180:  # 3 minutes timeout
        history = requests.get(f"{COMFYUI_URL}/history/{prompt_id}").json()
        
        if prompt_id in history:
            if "outputs" in history[prompt_id]:
                exec_time = time.time() - start_time
                print(f"\n✅ Complete in {exec_time:.1f} seconds!")
                
                outputs = history[prompt_id]["outputs"]
                for node_id, output in outputs.items():
                    if "images" in output:
                        for img in output["images"]:
                            print(f"  📹 Output: {img['filename']}")
                
                return True
        
        print(".", end="", flush=True)
        time.sleep(2)
    
    print("\n❌ Timeout")
    return False

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║         WAN2.1 FLF GGUF - First-Last Frame Test         ║
║                    24GB VRAM Optimized                   ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    success = test_flf_pipeline()
    
    if success:
        print("\n🎉 FLF GGUF implementation successful!")
        print("You can now generate smooth transitions between images.")
    else:
        print("\n❌ Test failed. Check the logs above.")
    
    sys.exit(0 if success else 1)