#!/usr/bin/env python3
"""
Simplified FLF worker that uses existing ComfyUI infrastructure
Based on working rapid-i2v implementation
"""

import os
import sys
import json
import time
import random
import base64
import requests
import subprocess
from typing import Dict, Any, Optional

# Import RunPod
import runpod

# Configuration
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://localhost:8188")

def check_comfyui_server():
    """Check if ComfyUI server is available"""
    try:
        response = requests.get(f"{COMFYUI_URL}/system_stats", timeout=5)
        return response.status_code == 200
    except:
        return False

def queue_prompt(prompt):
    """Queue a prompt to ComfyUI"""
    p = {"prompt": prompt}
    response = requests.post(f"{COMFYUI_URL}/prompt", json=p)
    return response.json()

def get_image(filename, subfolder, folder_type):
    """Get image from ComfyUI output"""
    response = requests.get(f"{COMFYUI_URL}/view", params={
        "filename": filename,
        "subfolder": subfolder,
        "type": folder_type
    })
    return response.content

def get_history(prompt_id):
    """Get history for a prompt"""
    response = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
    return response.json()

def upload_image(image_data, filename):
    """Upload an image to ComfyUI"""
    files = {"image": (filename, image_data, "image/png")}
    data = {"overwrite": "true"}
    response = requests.post(f"{COMFYUI_URL}/upload/image", files=files, data=data)
    return response.json()

def download_image_from_url(url):
    """Download image from URL"""
    response = requests.get(url)
    return response.content

def generate(job):
    """Main generation function for RunPod"""
    try:
        job_input = job.get("input", {})
        
        # Get parameters
        start_image = job_input.get("start_image", "")
        end_image = job_input.get("end_image", "")
        positive_prompt = job_input.get("positive_prompt", "smooth transition between frames")
        negative_prompt = job_input.get("negative_prompt", "static, blurry, low quality")
        width = job_input.get("width", 576)
        height = job_input.get("height", 576)
        length = job_input.get("length", 49)
        seed = job_input.get("seed", random.randint(0, 2**32-1))
        
        # Check ComfyUI server
        if not check_comfyui_server():
            # Try to start ComfyUI
            print("Starting ComfyUI server...")
            subprocess.Popen(["python", "/comfyui/main.py", "--listen", "--port", "8188"])
            time.sleep(10)
            
            if not check_comfyui_server():
                return {"error": "ComfyUI server not available"}
        
        # Handle image uploads
        start_image_name = "start_image.png"
        end_image_name = "end_image.png"
        
        if start_image.startswith(("http://", "https://")):
            image_data = download_image_from_url(start_image)
            upload_result = upload_image(image_data, start_image_name)
            start_image_name = upload_result.get("name", start_image_name)
        
        if end_image.startswith(("http://", "https://")):
            image_data = download_image_from_url(end_image)
            upload_result = upload_image(image_data, end_image_name)
            end_image_name = upload_result.get("name", end_image_name)
        
        # Load workflow template
        workflow_path = "/workflow.json"
        if os.path.exists(workflow_path):
            with open(workflow_path, 'r') as f:
                workflow = json.load(f)
        else:
            # Create a minimal FLF workflow
            workflow = create_minimal_flf_workflow()
        
        # Update workflow parameters
        update_workflow_params(workflow, {
            "start_image": start_image_name,
            "end_image": end_image_name,
            "positive_prompt": positive_prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "length": length,
            "seed": seed
        })
        
        # Queue the workflow
        result = queue_prompt(workflow)
        prompt_id = result.get('prompt_id')
        
        if not prompt_id:
            return {"error": "Failed to queue workflow"}
        
        # Wait for completion
        max_wait = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            history = get_history(prompt_id)
            
            if prompt_id in history:
                outputs = history[prompt_id].get('outputs', {})
                
                # Look for video output
                for node_id, node_output in outputs.items():
                    if 'gifs' in node_output:
                        for video in node_output['gifs']:
                            video_data = get_image(
                                video['filename'],
                                video.get('subfolder', ''),
                                video.get('type', 'output')
                            )
                            
                            # Encode to base64
                            video_base64 = base64.b64encode(video_data).decode('utf-8')
                            
                            return {
                                "video": video_base64,
                                "filename": video['filename'],
                                "seed": seed,
                                "status": "success"
                            }
            
            time.sleep(2)
        
        return {"error": "Generation timeout"}
        
    except Exception as e:
        print(f"Error in generate: {str(e)}")
        return {"error": str(e)}

def create_minimal_flf_workflow():
    """Create a minimal FLF workflow if template is missing"""
    return {
        "52": {
            "inputs": {"image": "start_image.png", "upload": "image"},
            "class_type": "LoadImage"
        },
        "67": {
            "inputs": {"image": "end_image.png", "upload": "image"},
            "class_type": "LoadImage"
        },
        "6": {
            "inputs": {"text": "smooth transition", "clip": ["38", 0]},
            "class_type": "CLIPTextEncode"
        },
        "7": {
            "inputs": {"text": "static, blurry", "clip": ["38", 0]},
            "class_type": "CLIPTextEncode"
        },
        "66": {
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "vae": ["39", 0],
                "start_image": ["52", 0],
                "end_image": ["67", 0],
                "width": 576,
                "height": 576,
                "length": 49,
                "batch_size": 1
            },
            "class_type": "WanFirstLastFrameToVideo"
        }
    }

def update_workflow_params(workflow, params):
    """Update workflow with provided parameters"""
    # Find and update relevant nodes
    for node_id, node in workflow.items():
        if node.get("class_type") == "LoadImage":
            if "start" in str(node_id) or node_id == "52":
                node["inputs"]["image"] = params["start_image"]
            elif "end" in str(node_id) or node_id == "67":
                node["inputs"]["image"] = params["end_image"]
        
        elif node.get("class_type") == "CLIPTextEncode":
            if "positive" in str(node.get("title", "")).lower() or node_id == "6":
                node["inputs"]["text"] = params["positive_prompt"]
            elif "negative" in str(node.get("title", "")).lower() or node_id == "7":
                node["inputs"]["text"] = params["negative_prompt"]
        
        elif node.get("class_type") == "WanFirstLastFrameToVideo":
            node["inputs"]["width"] = params["width"]
            node["inputs"]["height"] = params["height"]
            node["inputs"]["length"] = params["length"]
        
        elif node.get("class_type") == "KSamplerAdvanced":
            node["inputs"]["seed"] = params["seed"]

# RunPod handler
runpod.serverless.start({"handler": generate})