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

# Load FLF models
with torch.inference_mode():
    # Load FLF model for First-Last Frame processing
    unet = UNETLoader.load_unet("Wan2.1-FLF2V-14B-720P", "default")[0]
    clip = CLIPLoader.load_clip("Wan2.1-FLF2V-14B-720P/models_clip_open-clip-xlm-roberta-large-vit-huge-14.pth", "sd1", "default")[0]
    vae = VAELoader.load_vae("Wan2.1-FLF2V-14B-720P/Wan2.1_VAE.pth")[0]

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
    
    # It's a URL, download it
    print(f"Downloading image from URL: {input_image}")
    os.makedirs("/content/ComfyUI/input", exist_ok=True)
    file_suffix = os.path.splitext(urlsplit(input_image).path)[1]
    if not file_suffix:
        file_suffix = '.jpg'  # Default extension
    file_name_with_suffix = f"downloaded_image{file_suffix}"
    file_path = os.path.join("/content/ComfyUI/input", file_name_with_suffix)
    
    response = requests.get(input_image)
    response.raise_for_status()
    with open(file_path, 'wb') as file:
        file.write(response.content)
    print(f"Image downloaded to: {file_path}")
    return file_path

def images_to_mp4(images, output_path, fps=24):
    try:
        frames = []
        for image in images:
            i = 255. * image.cpu().numpy()
            img = np.clip(i, 0, 255).astype(np.uint8)
            if img.shape[0] in [1, 3, 4]:
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

        # Apply model sampling to FLF model
        model = ModelSamplingSD3.patch(unet, shift)[0]
        
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
        
        # Single-stage sampling with FLF model
        out_samples = KSamplerAdvanced.sample(
            model, seed, 20, cfg, "euler", "simple",
            positive, negative, out_latent,
            add_noise="enable", noise_seed=seed, start_at_step=0, end_at_step=20, return_with_leftover_noise="disable"
        )[0]

        decoded_images = VAEDecode.decode(vae, out_samples)[0].detach()
        
        # Create output directory and save video locally
        os.makedirs("/content/ComfyUI/output", exist_ok=True)
        result = f"/content/ComfyUI/output/wan2.2-flf-{seed}-local.mp4"
        images_to_mp4(decoded_images, result, fps)
        
        job_id = values.get('job_id', f'flf-job-{seed}')
        
        # Calculate execution time
        execution_time = round(time.time() - start_time, 2)
        
        # Return local file path with execution time
        return {
            "jobId": job_id,
            "result": result,
            "status": "DONE",
            "message": "FLF video saved locally",
            "execution_time": execution_time
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