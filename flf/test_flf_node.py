#!/usr/bin/env python3
"""
Test the WanFirstLastFrameToVideo node directly
"""

import json
import requests
import time
import os

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
        files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
        data = {"overwrite": "true"}
        response = requests.post(f"{COMFYUI_URL}/upload/image", files=files, data=data)
        return response.json()

def test_wan_flf():
    """Test WanFirstLastFrameToVideo node"""
    
    print("🎬 Testing WanFirstLastFrameToVideo node...")
    
    # Upload test images
    start_image_path = "/home/kazuph/runpod-wan2.2-api/rapid-i2v/input/girl1.jpg"
    end_image_path = "/home/kazuph/runpod-wan2.2-api/rapid-i2v/input/girl2.jpg"
    
    print(f"📤 Uploading start image...")
    start_upload = upload_image(start_image_path)
    start_image_name = start_upload.get("name", "girl1.jpg")
    
    print(f"📤 Uploading end image...")
    end_upload = upload_image(end_image_path)
    end_image_name = end_upload.get("name", "girl2.jpg")
    
    # Create FLF workflow using the actual WanFirstLastFrameToVideo node
    workflow = {
        # Load CLIP (using existing model)
        "1": {
            "inputs": {
                "clip_name": "clip_vit_h.safetensors",
                "type": "sd3"
            },
            "class_type": "CLIPLoader",
            "_meta": {"title": "Load CLIP"}
        },
        
        # Load VAE
        "2": {
            "inputs": {
                "vae_name": "Wan2.2_VAE.pth"
            },
            "class_type": "VAELoader",
            "_meta": {"title": "Load VAE"}
        },
        
        # Load UNet model (using rapid model as fallback)
        "3": {
            "inputs": {
                "unet_name": "wan2.2-i2v-rapid.safetensors",
                "weight_dtype": "default"
            },
            "class_type": "UNETLoader",
            "_meta": {"title": "Load UNET"}
        },
        
        # Load start image
        "4": {
            "inputs": {
                "image": start_image_name,
                "upload": "image"
            },
            "class_type": "LoadImage",
            "_meta": {"title": "Load Start Image"}
        },
        
        # Load end image
        "5": {
            "inputs": {
                "image": end_image_name,
                "upload": "image"
            },
            "class_type": "LoadImage",
            "_meta": {"title": "Load End Image"}
        },
        
        # Positive prompt
        "6": {
            "inputs": {
                "text": "smooth morphing transition between two beautiful faces, gradual transformation, natural movement, high quality",
                "clip": ["1", 0]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "Positive Prompt"}
        },
        
        # Negative prompt
        "7": {
            "inputs": {
                "text": "static, blurry, distortion, abrupt change, low quality, mouth opening, talking",
                "clip": ["1", 0]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "Negative Prompt"}
        },
        
        # WanFirstLastFrameToVideo node
        "8": {
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "vae": ["2", 0],
                "start_image": ["4", 0],
                "end_image": ["5", 0],
                "width": 576,
                "height": 576,
                "length": 49,  # ~2 seconds at 24fps
                "batch_size": 1
            },
            "class_type": "WanFirstLastFrameToVideo",
            "_meta": {"title": "FLF Video Generation"}
        },
        
        # Model Sampling
        "9": {
            "inputs": {
                "model": ["3", 0],
                "shift": 8.0
            },
            "class_type": "ModelSamplingSD3",
            "_meta": {"title": "Model Sampling"}
        },
        
        # KSampler
        "10": {
            "inputs": {
                "model": ["9", 0],
                "positive": ["8", 0],
                "negative": ["8", 1],
                "latent_image": ["8", 2],
                "seed": 42,
                "steps": 20,
                "cfg": 4.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0
            },
            "class_type": "KSampler",
            "_meta": {"title": "KSampler"}
        },
        
        # VAE Decode
        "11": {
            "inputs": {
                "samples": ["10", 0],
                "vae": ["2", 0]
            },
            "class_type": "VAEDecode",
            "_meta": {"title": "VAE Decode"}
        },
        
        # Save images (will create multiple frames)
        "12": {
            "inputs": {
                "images": ["11", 0],
                "filename_prefix": "wan_flf_test"
            },
            "class_type": "SaveImage",
            "_meta": {"title": "Save Images"}
        }
    }
    
    # Queue the workflow
    print("\n🚀 Queuing FLF workflow...")
    result = queue_prompt(workflow)
    prompt_id = result.get('prompt_id')
    
    if not prompt_id:
        error_msg = result.get('error', result)
        print(f"❌ Failed to queue workflow: {error_msg}")
        
        # If there's a node error, print more details
        if 'node_errors' in result:
            for node_id, errors in result['node_errors'].items():
                print(f"  Node {node_id} errors:")
                for error in errors:
                    print(f"    - {error}")
        
        return False
    
    print(f"📋 Prompt ID: {prompt_id}")
    print("⏳ Waiting for completion...")
    
    # Wait for completion
    max_wait = 120  # 2 minutes
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < max_wait:
        history = get_history(prompt_id)
        
        if prompt_id in history:
            status_info = history[prompt_id].get('status', {})
            status = status_info.get('status_str', 'unknown')
            
            if status != last_status:
                print(f"  Status: {status}")
                last_status = status
            
            if status == 'success':
                print("\n✅ FLF video generation completed successfully!")
                
                outputs = history[prompt_id].get('outputs', {})
                for node_id, output in outputs.items():
                    if 'gifs' in output:
                        for video in output['gifs']:
                            filename = video['filename']
                            print(f"  🎥 Output video: {filename}")
                            
                            # Check file size
                            output_path = f"/home/kazuph/runpod-wan2.2-api/comfyui_workflow/comfyui_workflow/output/{filename}"
                            if os.path.exists(output_path):
                                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                                print(f"  📊 File size: {size_mb:.2f} MB")
                
                return True
                
            elif status == 'error':
                print(f"\n❌ Workflow failed")
                
                # Get error details
                if 'status' in history[prompt_id]:
                    messages = history[prompt_id]['status'].get('messages', [])
                    for msg in messages:
                        print(f"  Error: {msg}")
                
                return False
        
        time.sleep(2)
    
    print("\n❌ Workflow timeout after 2 minutes")
    return False

if __name__ == "__main__":
    success = test_wan_flf()
    exit(0 if success else 1)