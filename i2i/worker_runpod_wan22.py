import os, json, requests, random, time, runpod
from PIL import Image
from urllib.parse import urlsplit

import torch
import numpy as np

from nodes import NODE_CLASS_MAPPINGS
from comfy_extras import nodes_wan

# Initialize nodes for WAN2.2
UNETLoader = NODE_CLASS_MAPPINGS["UNETLoader"]()
VAELoader = NODE_CLASS_MAPPINGS["VAELoader"]()
CLIPLoader = NODE_CLASS_MAPPINGS["CLIPLoader"]()
CLIPTextEncode = NODE_CLASS_MAPPINGS["CLIPTextEncode"]()
LoadImage = NODE_CLASS_MAPPINGS["LoadImage"]()
EmptyLatentImage = NODE_CLASS_MAPPINGS["EmptyLatentImage"]()
VAEEncode = NODE_CLASS_MAPPINGS["VAEEncode"]()
VAEDecode = NODE_CLASS_MAPPINGS["VAEDecode"]()
KSamplerAdvanced = NODE_CLASS_MAPPINGS["KSamplerAdvanced"]()
Wan22ImageToVideoLatent = nodes_wan.NODE_CLASS_MAPPINGS["Wan22ImageToVideoLatent"]()

# Load models
with torch.inference_mode():
    # Load WAN2.2 models using proper paths
    unet = UNETLoader.load_unet("wan2.2_ti2v_5B_fp16.safetensors", "default")[0]
    vae = VAELoader.load_vae("wan2.2_vae.safetensors")[0]
    clip = CLIPLoader.load_clip("umt5_xxl_fp8_e4m3fn_scaled.safetensors", "wan22", "default")[0]

def get_input_image_path(input_image):
    """Get the path to the input image."""
    if not input_image.startswith(('http://', 'https://')):
        local_path = f"/content/ComfyUI/input/{input_image}"
        if os.path.exists(local_path):
            print(f"Using local image: {local_path}")
            return local_path
        else:
            if os.path.exists(input_image):
                print(f"Using absolute path image: {input_image}")
                return input_image
            else:
                raise FileNotFoundError(f"Local image not found: {input_image}")
    
    print(f"Downloading image from URL: {input_image}")
    os.makedirs("/content/ComfyUI/input", exist_ok=True)
    file_suffix = os.path.splitext(urlsplit(input_image).path)[1]
    if not file_suffix:
        file_suffix = '.jpg'
    file_name_with_suffix = f"downloaded_image{file_suffix}"
    file_path = os.path.join("/content/ComfyUI/input", file_name_with_suffix)
    
    response = requests.get(input_image)
    response.raise_for_status()
    with open(file_path, 'wb') as file:
        file.write(response.content)
    print(f"Image downloaded to: {file_path}")
    return file_path

def save_image(images, output_path):
    """Save the first frame as a static image"""
    try:
        # Handle video tensor format - extract first frame
        if len(images.shape) == 5:  # batch, frames, channels, height, width
            first_frame = images[0, 0]
        elif len(images.shape) == 4:  # batch, channels, height, width
            first_frame = images[0]
        else:
            first_frame = images
            
        i = 255. * first_frame.cpu().numpy()
        img = np.clip(i, 0, 255).astype(np.uint8)
        
        if img.shape[0] in [1, 3, 4]:
            img = np.transpose(img, (1, 2, 0))
        
        if img.shape[-1] == 4:
            pil_img = Image.fromarray(img, mode='RGBA')
        elif img.shape[-1] == 3:
            pil_img = Image.fromarray(img, mode='RGB')
        elif len(img.shape) == 2:
            pil_img = Image.fromarray(img, mode='L')
        else:
            raise ValueError(f"Unexpected image shape: {img.shape}")
        
        pil_img.save(output_path, 'PNG', optimize=True)
        print(f"Static image saved to: {output_path}")
        
    except Exception as e:
        print(f"Error saving image: {e}")
        raise

@torch.inference_mode()
def generate(input):
    start_time = time.time()
    
    try:
        values = input["input"]

        # Common parameters
        positive_prompt = values['positive_prompt']
        negative_prompt = values.get('negative_prompt', '')
        width = values.get('width', 576)
        height = values.get('height', 576)
        seed = values.get('seed', 0)
        if seed == 0:
            random.seed(int(time.time()))
            seed = random.randint(0, 18446744073709551615)
        
        # Check if this is T2I or I2I
        input_image_param = values.get('input_image', None)
        is_t2i = input_image_param is None or input_image_param == ""
        
        # Encode prompts
        positive = CLIPTextEncode.encode(clip, positive_prompt)[0]
        negative = CLIPTextEncode.encode(clip, negative_prompt)[0]
        
        if is_t2i:
            print(f"Generating T2I (text-to-image) with prompt: {positive_prompt}")
            print(f"Resolution: {width}x{height}, Seed: {seed}")
            
            # T2I workflow - create empty latent with WAN22
            latent = Wan22ImageToVideoLatent.encode(
                positive, negative, vae, 
                width, height, 
                length=1,  # 1 frame for static image
                batch_size=1,
                start_image=None  # No start image for T2I
            )[2]  # Returns (positive, negative, latent)
            
        else:
            print(f"Generating I2I (image-to-image) with prompt: {positive_prompt}")
            print(f"Resolution: {width}x{height}, Seed: {seed}")
            
            # I2I workflow - encode input image with WAN22
            input_image_path = get_input_image_path(input_image_param)
            input_image = LoadImage.load_image(input_image_path)[0]
            positive, negative, latent = Wan22ImageToVideoLatent.encode(
                positive, negative, vae,
                width, height,
                length=1,  # 1 frame for static image
                batch_size=1,
                start_image=input_image
            )
        
        # Run sampling
        steps = values.get('steps', 28)
        cfg = values.get('cfg', 1.0)
        sampler_name = values.get('sampler_name', 'euler')
        scheduler = values.get('scheduler', 'beta')
        
        samples = KSamplerAdvanced.sample(
            model=unet,
            add_noise="enable",
            noise_seed=seed,
            steps=steps,
            cfg=cfg,
            sampler_name=sampler_name,
            scheduler=scheduler,
            positive=positive,
            negative=negative,
            latent_image=latent,
            start_at_step=0,
            end_at_step=steps,
            return_with_leftover_noise="disable"
        )[0]
        
        # Decode
        decoded_images = VAEDecode.decode(vae, samples)[0].detach()
        
        # Save static image
        os.makedirs("/content/ComfyUI/output", exist_ok=True)
        mode_prefix = "t2i" if is_t2i else "i2i"
        result = f"/content/ComfyUI/output/wan2.2-{mode_prefix}-{seed}-local.png"
        save_image(decoded_images, result)
        
        job_id = values.get('job_id', f'local-job-{seed}')
        execution_time = round(time.time() - start_time, 2)
        
        return {
            "jobId": job_id,
            "result": result,
            "status": "DONE",
            "message": f"{'T2I' if is_t2i else 'I2I'} image generated successfully",
            "execution_time": execution_time
        }
    except Exception as e:
        job_id = values.get('job_id', 'unknown-job') if 'values' in locals() else 'unknown-job'
        print(f"Error in generate: {str(e)}")
        import traceback
        traceback.print_exc()
        execution_time = round(time.time() - start_time, 2)
        return {
            "jobId": job_id,
            "result": f"FAILED: {str(e)}",
            "status": "FAILED",
            "execution_time": execution_time
        }

runpod.serverless.start({"handler": generate})