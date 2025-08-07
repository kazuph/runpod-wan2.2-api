import os, json, requests, random, time, cv2, ffmpeg, runpod
from moviepy.video.io.VideoFileClip import VideoFileClip
from urllib.parse import urlsplit

import sys
sys.path.append('/content/ComfyUI')

import torch
import numpy as np

from nodes import NODE_CLASS_MAPPINGS
from comfy_extras import nodes_wan, nodes_model_advanced

# Load FLF-specific nodes and components
UNETLoader = NODE_CLASS_MAPPINGS["UNETLoader"]()
CLIPLoader = NODE_CLASS_MAPPINGS["CLIPLoader"]()
VAELoader = NODE_CLASS_MAPPINGS["VAELoader"]()
LoadImage = NODE_CLASS_MAPPINGS["LoadImage"]()
CLIPTextEncode = NODE_CLASS_MAPPINGS["CLIPTextEncode"]()
WanFirstLastFrameToVideo = nodes_wan.NODE_CLASS_MAPPINGS["WanFirstLastFrameToVideo"]()
KSamplerAdvanced = NODE_CLASS_MAPPINGS["KSamplerAdvanced"]()
ModelSamplingSD3 = nodes_model_advanced.NODE_CLASS_MAPPINGS["ModelSamplingSD3"]()
VAEDecode = NODE_CLASS_MAPPINGS["VAEDecode"]()

# Check which workflow to use based on environment variable
USE_OFFICIAL_WORKFLOW = os.getenv("USE_OFFICIAL_WORKFLOW", "true").lower() == "true"

# Load FLF models based on workflow choice
with torch.inference_mode():
    if USE_OFFICIAL_WORKFLOW:
        print("Loading official WAN2.2 FLF2V models...")
        # Load high and low noise models for dual-stage sampling
        unet_high = UNETLoader.load_unet("wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors", "default")[0]
        unet_low = UNETLoader.load_unet("wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors", "default")[0]
        
        # Load CLIP text encoder
        clip = CLIPLoader.load_clip("umt5_xxl_fp8_e4m3fn_scaled.safetensors", "wan", "default")[0]
        
        # Load VAE
        vae = VAELoader.load_vae("wan_2.1_vae.safetensors")[0]
    else:
        print("Loading existing FLF models...")
        # Load existing models (with _KJ suffix)
        unet_high = UNETLoader.load_unet("Wan2_2-I2V-A14B-HIGH_fp8_e4m3fn_scaled_KJ.safetensors", "default")[0]
        unet_low = UNETLoader.load_unet("Wan2_2-I2V-A14B-LOW_fp8_e4m3fn_scaled_KJ.safetensors", "default")[0]
        
        # Load CLIP text encoder
        clip = CLIPLoader.load_clip("umt5_xxl_fp8_e4m3fn_scaled.safetensors", "wan", "default")[0]
        
        # Load VAE
        vae = VAELoader.load_vae("wan_2.1_vae.safetensors")[0]

def get_input_image_path(input_image):
    """
    Get the path to the input image.
    Supports both URLs and local file paths.
    """
    # Check if it's a local file path
    if not input_image.startswith(('http://', 'https://')):
        # Assume it's a local file path relative to /content/ComfyUI/input/
        local_path = f"/content/ComfyUI/input/{input_image}"
        if os.path.exists(local_path):
            print(f"Using local image: {local_path}")
            return local_path
        else:
            # Check if it's an absolute path
            if os.path.exists(input_image):
                print(f"Using absolute path image: {input_image}")
                return input_image
            else:
                raise FileNotFoundError(f"Local image not found: {input_image}")
    
    # Handle URLs
    image_filename = os.path.basename(urlsplit(input_image).path) or "temp_image.png"
    image_path = f"/content/ComfyUI/input/{image_filename}"
    
    # Download the image
    response = requests.get(input_image)
    response.raise_for_status()
    
    # Save image locally
    with open(image_path, 'wb') as f:
        f.write(response.content)
    
    print(f"Downloaded and saved image: {image_path}")
    return image_path

def images_to_mp4(images, output_path, fps=24):
    try:
        frames = []
        for img in images:
            img = img.numpy() * 255
            img = img.astype(np.uint8)
            if img.shape[0] == 3:
                img = np.transpose(img, (1, 2, 0))
            if img.shape[-1] == 4:
                img = img[:, :, :3]
            frames.append(img)
        temp_files = [f"temp_{i:04d}.png" for i in range(len(frames))]
        for i, frame in enumerate(frames):
            success = cv2.imwrite(temp_files[i], frame[:, :, ::-1])
            if not success:
                raise ValueError(f"Failed to write {temp_files[i]}")
        if not os.path.exists(temp_files[0]):
            raise FileNotFoundError("Temporary PNG files were not created")
        stream = ffmpeg.input('temp_%04d.png', framerate=fps)
        stream = ffmpeg.output(stream, output_path, vcodec='libx264', pix_fmt='yuv420p')
        ffmpeg.run(stream, overwrite_output=True)
        for temp_file in temp_files:
            os.remove(temp_file)
    except Exception as e:
        print(f"Error: {e}")

@torch.inference_mode()
def generate(input):
    # Start timing the entire generation process
    start_time = time.time()
    
    try:
        values = input["input"]

        # FLF-specific parameters
        start_image = values['start_image']
        end_image = values['end_image']
        start_image_path = get_input_image_path(start_image)
        end_image_path = get_input_image_path(end_image)
        
        positive_prompt = values['positive_prompt']
        negative_prompt = values['negative_prompt']
        width = values['width']
        height = values['height']
        length = values['length']
        batch_size = values.get('batch_size', 1)
        shift = values.get('shift', 8.0)
        cfg = values.get('cfg', 4.0)
        seed = values['seed']
        if seed == 0:
            random.seed(int(time.time()))
            seed = random.randint(0, 18446744073709551615)
        fps = values.get('fps', 24)

        # Apply model sampling to both high and low noise models
        model_high = ModelSamplingSD3.patch(unet_high, shift)[0]
        model_low = ModelSamplingSD3.patch(unet_low, shift)[0]
        
        # Encode prompts
        positive = CLIPTextEncode.encode(clip, positive_prompt)[0]
        negative = CLIPTextEncode.encode(clip, negative_prompt)[0]

        # Load start and end images
        start_img = LoadImage.load_image(start_image_path)[0]
        end_img = LoadImage.load_image(end_image_path)[0]

        # Use WanFirstLastFrameToVideo for FLF processing
        positive, negative, out_latent = WanFirstLastFrameToVideo.encode(
            positive, negative, vae, width, height, length, batch_size,
            start_image=start_img, end_image=end_img
        )
        
        # Dual-stage sampling: First with high noise model (steps 0-10)
        intermediate_samples = KSamplerAdvanced.sample(
            model_high, seed, 20, cfg, "euler", "simple",
            positive, negative, out_latent,
            add_noise="enable", noise_seed=seed, start_at_step=0, end_at_step=10, return_with_leftover_noise="enable"
        )[0]
        
        # Second stage with low noise model (steps 10-20)
        out_samples = KSamplerAdvanced.sample(
            model_low, seed, 20, cfg, "euler", "simple",
            positive, negative, intermediate_samples,
            add_noise="disable", noise_seed=seed, start_at_step=10, end_at_step=10000, return_with_leftover_noise="disable"
        )[0]

        decoded_images = VAEDecode.decode(vae, out_samples)[0].detach()
        
        # Create output directory and save video locally
        os.makedirs("/content/ComfyUI/output", exist_ok=True)
        workflow_type = "official" if USE_OFFICIAL_WORKFLOW else "existing"
        result = f"/content/ComfyUI/output/wan2.2-flf-{workflow_type}-{seed}-local.mp4"
        images_to_mp4(decoded_images, result, fps)
        
        job_id = values.get('job_id', f'flf-job-{seed}')
        
        # Calculate execution time
        execution_time = round(time.time() - start_time, 2)
        
        # Return local file path with execution time
        return {
            "jobId": job_id,
            "result": result,
            "status": "DONE",
            "message": f"FLF video saved locally (workflow: {workflow_type})",
            "execution_time": execution_time,
            "workflow_type": workflow_type
        }
    except Exception as e:
        job_id = values.get('job_id', 'unknown-flf-job') if 'values' in locals() else 'unknown-flf-job'
        print(f"Error in FLF generate: {str(e)}")
        execution_time = round(time.time() - start_time, 2)
        return {
            "jobId": job_id,
            "result": f"FAILED: {str(e)}",
            "status": "FAILED",
            "execution_time": execution_time
        }

runpod.serverless.start({"handler": generate})