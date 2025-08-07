#!/usr/bin/env python3
"""
RunPod Handler for WAN2.2 FLF (First-Last Frame) video generation
Based on Flux ComfyUI architecture pattern
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
from urllib.parse import urlsplit

# Add ComfyUI to path
sys.path.append('/comfyui')

# Import RunPod
import runpod

# ComfyUI API settings
COMFYUI_API_URL = "http://127.0.0.1:8188"

def check_server(url: str = COMFYUI_API_URL, retries: int = 500, delay: float = 0.05) -> bool:
    """Check if ComfyUI server is running"""
    for i in range(retries):
        try:
            response = requests.get(f"{url}/system_stats")
            if response.status_code == 200:
                print(f"ComfyUI server is ready at {url}")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if i % 10 == 0:
            print(f"Waiting for ComfyUI server... ({i}/{retries})")
        time.sleep(delay)
    
    print(f"Failed to connect to ComfyUI server at {url}")
    return False

def download_image(url: str, save_path: str) -> str:
    """Download image from URL and save to disk"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded image to {save_path}")
        return save_path
    except Exception as e:
        print(f"Failed to download image from {url}: {e}")
        raise

def upload_image(image_path: str, subfolder: str = "", overwrite: bool = True) -> Dict[str, Any]:
    """Upload image to ComfyUI server"""
    try:
        with open(image_path, 'rb') as f:
            files = {
                'image': (os.path.basename(image_path), f, 'image/png')
            }
            data = {
                'subfolder': subfolder,
                'overwrite': str(overwrite).lower()
            }
            
            response = requests.post(
                f"{COMFYUI_API_URL}/upload/image",
                files=files,
                data=data
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"Uploaded image: {result}")
            return result
    except Exception as e:
        print(f"Failed to upload image {image_path}: {e}")
        raise

def queue_workflow(workflow: Dict[str, Any]) -> str:
    """Queue workflow for execution"""
    try:
        payload = {
            "prompt": workflow,
            "client_id": f"runpod-{random.randint(1000, 9999)}"
        }
        
        response = requests.post(f"{COMFYUI_API_URL}/prompt", json=payload)
        response.raise_for_status()
        result = response.json()
        
        prompt_id = result.get('prompt_id')
        print(f"Queued workflow with prompt_id: {prompt_id}")
        return prompt_id
    except Exception as e:
        print(f"Failed to queue workflow: {e}")
        raise

def get_history(prompt_id: str, retries: int = 500, delay: float = 0.25) -> Optional[Dict[str, Any]]:
    """Get workflow execution history"""
    for i in range(retries):
        try:
            response = requests.get(f"{COMFYUI_API_URL}/history/{prompt_id}")
            if response.status_code == 200:
                history = response.json()
                if prompt_id in history and history[prompt_id].get('outputs'):
                    print(f"Workflow completed: {prompt_id}")
                    return history[prompt_id]
        except requests.exceptions.RequestException:
            pass
        
        if i % 10 == 0:
            print(f"Waiting for workflow completion... ({i}/{retries})")
        time.sleep(delay)
    
    print(f"Workflow timeout: {prompt_id}")
    return None

def process_output_videos(outputs: Dict[str, Any]) -> Optional[str]:
    """Process and return the output video path"""
    for node_id, node_output in outputs.items():
        if 'gifs' in node_output:
            for video in node_output['gifs']:
                video_path = f"/comfyui/output/{video['filename']}"
                if os.path.exists(video_path):
                    print(f"Found output video: {video_path}")
                    return video_path
    return None

def validate_input(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and extract input parameters"""
    # Required parameters
    required = ['start_image', 'end_image']
    for param in required:
        if param not in job_input:
            raise ValueError(f"Missing required parameter: {param}")
    
    # Extract parameters with defaults
    params = {
        'start_image': job_input['start_image'],
        'end_image': job_input['end_image'],
        'positive_prompt': job_input.get('positive_prompt', 'smooth transition animation between frames'),
        'negative_prompt': job_input.get('negative_prompt', 'static, blurry, low quality, mouth opening, talking'),
        'width': job_input.get('width', 720),
        'height': job_input.get('height', 1280),
        'length': job_input.get('length', 81),
        'batch_size': job_input.get('batch_size', 1),
        'seed': job_input.get('seed', random.randint(0, 2**32 - 1)),
        'fps': job_input.get('fps', 16),
        'steps': job_input.get('steps', 20),
        'cfg': job_input.get('cfg', 4.0),
        'sampler_name': job_input.get('sampler_name', 'euler'),
        'scheduler': job_input.get('scheduler', 'simple')
    }
    
    # If seed is 0, generate random seed
    if params['seed'] == 0:
        params['seed'] = random.randint(0, 2**32 - 1)
    
    return params

def prepare_workflow(params: Dict[str, Any], start_image_name: str, end_image_name: str) -> Dict[str, Any]:
    """Prepare the FLF workflow with dynamic parameters"""
    
    workflow = {
        # Load CLIP text encoder
        "38": {
            "inputs": {
                "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                "type": "wan",
                "key": "default"
            },
            "class_type": "CLIPLoader"
        },
        
        # Load VAE
        "39": {
            "inputs": {
                "vae_name": "wan2.2_vae.safetensors"
            },
            "class_type": "VAELoader"
        },
        
        # Load HIGH noise model
        "37": {
            "inputs": {
                "unet_name": "wan2.2-flf-high.safetensors",
                "weight_dtype": "fp8_e4m3fn"
            },
            "class_type": "UNETLoader"
        },
        
        # Load LOW noise model
        "56": {
            "inputs": {
                "unet_name": "wan2.2-flf-low.safetensors",
                "weight_dtype": "fp8_e4m3fn"
            },
            "class_type": "UNETLoader"
        },
        
        # Model sampling for HIGH noise
        "54": {
            "inputs": {
                "model": ["37", 0],
                "shift": 8.0
            },
            "class_type": "ModelSamplingSD3"
        },
        
        # Model sampling for LOW noise
        "55": {
            "inputs": {
                "model": ["56", 0],
                "shift": 8.0
            },
            "class_type": "ModelSamplingSD3"
        },
        
        # Load start image
        "52": {
            "inputs": {
                "image": start_image_name,
                "upload": "image"
            },
            "class_type": "LoadImage"
        },
        
        # Load end image
        "67": {
            "inputs": {
                "image": end_image_name,
                "upload": "image"
            },
            "class_type": "LoadImage"
        },
        
        # Positive prompt encoding
        "6": {
            "inputs": {
                "text": params['positive_prompt'],
                "clip": ["38", 0]
            },
            "class_type": "CLIPTextEncode"
        },
        
        # Negative prompt encoding
        "7": {
            "inputs": {
                "text": params['negative_prompt'],
                "clip": ["38", 0]
            },
            "class_type": "CLIPTextEncode"
        },
        
        # WAN First-Last Frame node
        "66": {
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "vae": ["39", 0],
                "start_image": ["52", 0],
                "end_image": ["67", 0],
                "width": params['width'],
                "height": params['height'],
                "length": params['length'],
                "batch_size": params['batch_size']
            },
            "class_type": "WanFirstLastFrameToVideo"
        },
        
        # First KSampler (HIGH noise, steps 0-10)
        "57": {
            "inputs": {
                "model": ["54", 0],
                "positive": ["66", 0],
                "negative": ["66", 1],
                "latent_image": ["66", 2],
                "seed": params['seed'],
                "steps": params['steps'],
                "cfg": params['cfg'],
                "sampler_name": params['sampler_name'],
                "scheduler": params['scheduler'],
                "add_noise": "enable",
                "noise_seed": params['seed'],
                "start_at_step": 0,
                "end_at_step": 10,
                "return_with_leftover_noise": "enable"
            },
            "class_type": "KSamplerAdvanced"
        },
        
        # Second KSampler (LOW noise, steps 10-20)
        "58": {
            "inputs": {
                "model": ["55", 0],
                "positive": ["66", 0],
                "negative": ["66", 1],
                "latent_image": ["57", 0],
                "seed": 0,
                "steps": params['steps'],
                "cfg": params['cfg'],
                "sampler_name": params['sampler_name'],
                "scheduler": params['scheduler'],
                "add_noise": "disable",
                "noise_seed": 0,
                "start_at_step": 10,
                "end_at_step": 10000,
                "return_with_leftover_noise": "disable"
            },
            "class_type": "KSamplerAdvanced"
        },
        
        # VAE Decode
        "8": {
            "inputs": {
                "samples": ["58", 0],
                "vae": ["39", 0]
            },
            "class_type": "VAEDecode"
        },
        
        # Video Combine
        "61": {
            "inputs": {
                "images": ["8", 0],
                "frame_rate": params['fps'],
                "loop_count": 0,
                "filename_prefix": f"wan-flf-{params['seed']}",
                "format": "video/h264-mp4",
                "pix_fmt": "yuv420p",
                "crf": 19,
                "save_metadata": True,
                "pingpong": False,
                "save_output": True
            },
            "class_type": "VHS_VideoCombine"
        }
    }
    
    return workflow

def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """RunPod handler function"""
    start_time = time.time()
    
    try:
        # Extract job input
        job_input = job.get('input', {})
        
        # Validate input
        params = validate_input(job_input)
        print(f"Processing FLF job with params: {params}")
        
        # Check if ComfyUI server is ready
        if not check_server():
            raise RuntimeError("ComfyUI server is not responding")
        
        # Handle start image
        start_image_name = "start_image.png"
        if params['start_image'].startswith(('http://', 'https://')):
            start_image_path = "/tmp/start_image.png"
            download_image(params['start_image'], start_image_path)
        else:
            start_image_path = params['start_image']
        
        # Handle end image
        end_image_name = "end_image.png"
        if params['end_image'].startswith(('http://', 'https://')):
            end_image_path = "/tmp/end_image.png"
            download_image(params['end_image'], end_image_path)
        else:
            end_image_path = params['end_image']
        
        # Upload images to ComfyUI
        start_upload = upload_image(start_image_path)
        start_image_name = start_upload['name']
        
        end_upload = upload_image(end_image_path)
        end_image_name = end_upload['name']
        
        # Prepare workflow
        workflow = prepare_workflow(params, start_image_name, end_image_name)
        
        # Queue workflow
        prompt_id = queue_workflow(workflow)
        
        # Wait for completion
        history = get_history(prompt_id)
        if not history:
            raise RuntimeError("Workflow execution timed out")
        
        # Process outputs
        outputs = history.get('outputs', {})
        video_path = process_output_videos(outputs)
        
        if not video_path:
            raise RuntimeError("No video output found")
        
        # Read video file and encode to base64
        with open(video_path, 'rb') as f:
            video_data = f.read()
            video_base64 = base64.b64encode(video_data).decode('utf-8')
        
        execution_time = round(time.time() - start_time, 2)
        
        return {
            "video": video_base64,
            "video_path": video_path,
            "seed": params['seed'],
            "execution_time": execution_time,
            "status": "success"
        }
        
    except Exception as e:
        execution_time = round(time.time() - start_time, 2)
        print(f"Error in handler: {str(e)}")
        return {
            "error": str(e),
            "execution_time": execution_time,
            "status": "failed"
        }

# RunPod serverless start
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})