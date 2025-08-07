#!/usr/bin/env python3
"""
Test FLF with GGUF quantized model
"""

import json
import requests
import time
import os
import sys

COMFYUI_URL = "http://localhost:8188"

def restart_comfyui():
    """Restart ComfyUI to load new custom nodes"""
    print("🔄 Restarting ComfyUI to load GGUF nodes...")
    try:
        # Send interrupt signal to reload
        response = requests.post(f"{COMFYUI_URL}/interrupt")
        time.sleep(5)
    except:
        pass

def check_gguf_nodes():
    """Check if GGUF nodes are available"""
    try:
        response = requests.get(f"{COMFYUI_URL}/object_info")
        nodes = response.json()
        
        gguf_nodes = [node for node in nodes.keys() if 'GGUF' in node]
        if gguf_nodes:
            print(f"✅ Found GGUF nodes: {', '.join(gguf_nodes)}")
            return True
        else:
            print("❌ GGUF nodes not found")
            return False
    except Exception as e:
        print(f"❌ Error checking nodes: {e}")
        return False

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

def test_gguf_flf():
    """Test FLF with GGUF model"""
    
    print("🎬 Testing WAN2.1 FLF with GGUF Q6_K Model")
    print("=" * 50)
    
    # Check if ComfyUI is running
    try:
        response = requests.get(f"{COMFYUI_URL}/system_stats")
        print("✅ ComfyUI is running")
    except:
        print("❌ ComfyUI not accessible")
        return False
    
    # Check if GGUF nodes are available
    if not check_gguf_nodes():
        restart_comfyui()
        time.sleep(5)
        if not check_gguf_nodes():
            print("❌ GGUF nodes still not available after restart")
            return False
    
    # Check if GGUF model exists
    model_path = "/home/kazuph/runpod-wan2.2-api/flf/models/unet_gguf/Wan2.1-FLF2V-14B-720P-Q6_K.gguf"
    if os.path.exists(model_path):
        size_gb = os.path.getsize(model_path) / (1024**3)
        print(f"✅ GGUF model found: {size_gb:.2f} GB")
    else:
        print("❌ GGUF model not found. Please wait for download to complete.")
        return False
    
    # Upload test images
    start_image_path = "/home/kazuph/runpod-wan2.2-api/rapid-i2v/input/girl1.jpg"
    end_image_path = "/home/kazuph/runpod-wan2.2-api/rapid-i2v/input/girl2.jpg"
    
    print("\n📤 Uploading images...")
    start_upload = upload_image(start_image_path)
    start_image_name = start_upload.get("name", "girl1.jpg")
    
    end_upload = upload_image(end_image_path)
    end_image_name = end_upload.get("name", "girl2.jpg")
    
    # Load workflow template
    workflow_path = "/home/kazuph/runpod-wan2.2-api/flf/wan_flf_gguf_workflow.json"
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    # Update image names in workflow
    workflow["4"]["inputs"]["image"] = start_image_name
    workflow["5"]["inputs"]["image"] = end_image_name
    
    # Update prompt
    workflow["6"]["inputs"]["text"] = "beautiful morphing transition between two women faces, smooth gradual transformation, high quality animation"
    workflow["7"]["inputs"]["text"] = "static, blurry, distortion, abrupt change, low quality, artifacts"
    
    # Set parameters for 24GB VRAM
    workflow["8"]["inputs"]["width"] = 576  # Safe for 24GB
    workflow["8"]["inputs"]["height"] = 576
    workflow["8"]["inputs"]["length"] = 49  # ~2 seconds
    
    print("\n🚀 Queuing FLF GGUF workflow...")
    print(f"  Model: Wan2.1-FLF2V-14B-720P-Q6_K.gguf")
    print(f"  Resolution: 576x576")
    print(f"  Frames: 49")
    
    result = queue_prompt(workflow)
    prompt_id = result.get('prompt_id')
    
    if not prompt_id:
        error_msg = result.get('error', result)
        print(f"❌ Failed to queue workflow: {error_msg}")
        
        if 'node_errors' in result:
            for node_id, errors in result['node_errors'].items():
                print(f"  Node {node_id} errors: {errors}")
        
        return False
    
    print(f"📋 Prompt ID: {prompt_id}")
    print("⏳ Processing (this may take 2-3 minutes)...")
    
    # Wait for completion
    max_wait = 300  # 5 minutes
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < max_wait:
        history = get_history(prompt_id)
        
        if prompt_id in history:
            status_info = history[prompt_id].get('status', {})
            
            # Check execution messages
            if 'execution_time' in history[prompt_id]:
                exec_time = history[prompt_id]['execution_time']
                print(f"\n✅ FLF generation completed in {exec_time:.2f} seconds!")
                
                outputs = history[prompt_id].get('outputs', {})
                for node_id, output in outputs.items():
                    if 'images' in output:
                        for img in output['images']:
                            print(f"  🎥 Output: {img['filename']}")
                
                return True
            
            # Check for errors
            messages = status_info.get('messages', [])
            for msg in messages:
                if isinstance(msg, list) and len(msg) > 1:
                    msg_type = msg[0]
                    msg_data = msg[1]
                    
                    if msg_type == 'execution_error':
                        print(f"\n❌ Execution error: {msg_data}")
                        return False
                    elif msg_type == 'execution_cached':
                        print("  Using cached result...")
        
        time.sleep(2)
        print(".", end="", flush=True)
    
    print("\n❌ Timeout after 5 minutes")
    return False

if __name__ == "__main__":
    success = test_gguf_flf()
    sys.exit(0 if success else 1)