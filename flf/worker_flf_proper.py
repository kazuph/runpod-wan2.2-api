#!/usr/bin/env python3
"""
Proper FLF Worker with direct video output in container
"""

import os
import sys
import json
import time
import random
import base64
import requests
import subprocess
import tempfile
from typing import Dict, Any

import runpod

# ComfyUI API
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")

def check_server():
    """Check if ComfyUI server is running"""
    try:
        response = requests.get(f"{COMFYUI_URL}/system_stats", timeout=5)
        return response.status_code == 200
    except:
        return False

def upload_image(image_data, filename):
    """Upload image to ComfyUI"""
    files = {"image": (filename, image_data, "image/png")}
    response = requests.post(f"{COMFYUI_URL}/upload/image", files=files)
    return response.json()

def queue_prompt(workflow):
    """Queue workflow to ComfyUI"""
    response = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
    return response.json()

def get_history(prompt_id):
    """Get workflow execution history"""
    response = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
    return response.json()

def frames_to_video_in_container(frame_pattern, output_path, fps=24):
    """Convert frames to video using ffmpeg IN CONTAINER"""
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-pattern_type", "sequence",
        "-i", frame_pattern,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "19",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")
    
    return output_path

def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """RunPod handler - all processing in container"""
    
    start_time = time.time()
    
    try:
        job_input = job.get("input", {})
        
        # Parameters
        start_image_data = job_input.get("start_image")  # base64 or URL
        end_image_data = job_input.get("end_image")      # base64 or URL
        positive_prompt = job_input.get("positive_prompt", "smooth morphing transition")
        negative_prompt = job_input.get("negative_prompt", "static, blurry")
        width = job_input.get("width", 512)
        height = job_input.get("height", 512)
        length = job_input.get("length", 49)  # frames
        fps = job_input.get("fps", 24)
        seed = job_input.get("seed", random.randint(0, 2**32-1))
        
        # Ensure ComfyUI is running
        if not check_server():
            # Start ComfyUI in container
            subprocess.Popen([
                "python", "/comfyui/main.py",
                "--disable-auto-launch",
                "--listen", "--port", "8188"
            ])
            
            # Wait for startup
            for _ in range(30):
                if check_server():
                    break
                time.sleep(1)
            else:
                raise RuntimeError("ComfyUI failed to start")
        
        # Handle image inputs (base64 decode if needed)
        if start_image_data.startswith("data:"):
            start_image_data = base64.b64decode(start_image_data.split(",")[1])
        elif start_image_data.startswith("http"):
            response = requests.get(start_image_data)
            start_image_data = response.content
        else:
            start_image_data = base64.b64decode(start_image_data)
        
        if end_image_data.startswith("data:"):
            end_image_data = base64.b64decode(end_image_data.split(",")[1])
        elif end_image_data.startswith("http"):
            response = requests.get(end_image_data)
            end_image_data = response.content
        else:
            end_image_data = base64.b64decode(end_image_data)
        
        # Upload images to ComfyUI
        start_upload = upload_image(start_image_data, "start.png")
        end_upload = upload_image(end_image_data, "end.png")
        
        # FLF workflow with GGUF quantized model
        workflow = {
            "1": {
                "inputs": {"ckpt_name": "wan2.1-flf.safetensors"},
                "class_type": "CheckpointLoaderSimple"
            },
            "2": {
                "inputs": {"image": start_upload["name"], "upload": "image"},
                "class_type": "LoadImage"
            },
            "3": {
                "inputs": {"image": end_upload["name"], "upload": "image"},
                "class_type": "LoadImage"
            },
            "4": {
                "inputs": {"text": positive_prompt, "clip": ["1", 1]},
                "class_type": "CLIPTextEncode"  
            },
            "5": {
                "inputs": {"text": negative_prompt, "clip": ["1", 1]},
                "class_type": "CLIPTextEncode"
            },
            "6": {
                "inputs": {
                    "positive": ["4", 0],
                    "negative": ["5", 0], 
                    "vae": ["1", 2],
                    "start_image": ["2", 0],
                    "end_image": ["3", 0],
                    "width": width,
                    "height": height,
                    "length": length,
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
                "inputs": {"samples": ["7", 0], "vae": ["1", 2]},
                "class_type": "VAEDecode"
            }
        }
        
        # Save frames
        workflow["9"] = {
            "inputs": {
                "images": ["8", 0],
                "filename_prefix": f"flf_{seed}"
            },
            "class_type": "SaveImage"
        }
        
        # Queue workflow
        result = queue_prompt(workflow)
        prompt_id = result.get("prompt_id")
        
        if not prompt_id:
            # VHS not available, fallback to SaveImage
            workflow["9"] = {
                "inputs": {
                    "images": ["8", 0],
                    "filename_prefix": f"flf_{seed}"
                },
                "class_type": "SaveImage"
            }
            
            result = queue_prompt(workflow)
            prompt_id = result.get("prompt_id")
            
            if not prompt_id:
                raise RuntimeError(f"Failed to queue workflow: {result}")
        
        # Wait for completion
        for _ in range(120):  # 2 minutes timeout
            history = get_history(prompt_id)
            
            if prompt_id in history and "outputs" in history[prompt_id]:
                outputs = history[prompt_id]["outputs"]
                
                # Check for direct video output (VHS)
                for node_id, output in outputs.items():
                    if "gifs" in output:
                        # Video was created directly
                        video_info = output["gifs"][0]
                        video_path = f"/comfyui/output/{video_info['filename']}"
                        
                        with open(video_path, "rb") as f:
                            video_base64 = base64.b64encode(f.read()).decode()
                        
                        return {
                            "video": video_base64,
                            "format": "mp4",
                            "seed": seed,
                            "execution_time": time.time() - start_time,
                            "status": "success"
                        }
                
                # Fallback: convert frames to video in container
                for node_id, output in outputs.items():
                    if "images" in output:
                        frames = output["images"]
                        if frames:
                            # Get frame pattern
                            first_frame = frames[0]["filename"]
                            frame_pattern = f"/comfyui/output/{first_frame.replace('00001', '%05d')}"
                            
                            # Create video IN CONTAINER
                            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                                video_path = tmp.name
                            
                            frames_to_video_in_container(frame_pattern, video_path, fps)
                            
                            # Read and encode video
                            with open(video_path, "rb") as f:
                                video_base64 = base64.b64encode(f.read()).decode()
                            
                            # Clean up
                            os.unlink(video_path)
                            
                            return {
                                "video": video_base64,
                                "format": "mp4",
                                "seed": seed,
                                "execution_time": time.time() - start_time,
                                "status": "success",
                                "note": "converted from frames in container"
                            }
                
                raise RuntimeError("No output found")
            
            time.sleep(1)
        
        raise RuntimeError("Workflow timeout")
        
    except Exception as e:
        return {
            "error": str(e),
            "execution_time": time.time() - start_time,
            "status": "failed"
        }

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})