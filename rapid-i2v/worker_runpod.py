import os, json, requests, random, time, cv2, ffmpeg, runpod
from moviepy.video.io.VideoFileClip import VideoFileClip
from urllib.parse import urlsplit

import torch
import numpy as np

from nodes import NODE_CLASS_MAPPINGS
from comfy_extras import nodes_wan, nodes_model_advanced

CheckpointLoaderSimple = NODE_CLASS_MAPPINGS["CheckpointLoaderSimple"]()
CLIPVisionLoader = NODE_CLASS_MAPPINGS["CLIPVisionLoader"]()

LoadImage = NODE_CLASS_MAPPINGS["LoadImage"]()
CLIPTextEncode = NODE_CLASS_MAPPINGS["CLIPTextEncode"]()
CLIPVisionEncode = NODE_CLASS_MAPPINGS["CLIPVisionEncode"]()
WanImageToVideo = nodes_wan.NODE_CLASS_MAPPINGS["WanImageToVideo"]()
KSampler = NODE_CLASS_MAPPINGS["KSampler"]()
ModelSamplingSD3 = nodes_model_advanced.NODE_CLASS_MAPPINGS["ModelSamplingSD3"]()
VAEDecode = NODE_CLASS_MAPPINGS["VAEDecode"]()

with torch.inference_mode():
    unet, clip, vae = CheckpointLoaderSimple.load_checkpoint("wan2.2-i2v-rapid-aio.safetensors")
    clip_vision = CLIPVisionLoader.load_clip("clip_vision_vit_h.safetensors")[0]

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

        input_image = values['input_image']
        input_image_path = get_input_image_path(input_image)
        positive_prompt = values['positive_prompt']
        negative_prompt = values['negative_prompt']
        crop = values['crop']
        width = values['width']
        height = values['height']
        length = values['length']
        batch_size = values['batch_size']
        shift = values['shift']
        cfg = values['cfg']
        sampler_name = values['sampler_name']
        scheduler = values['scheduler']
        steps = values['steps']
        seed = values['seed']
        if seed == 0:
            random.seed(int(time.time()))
            seed = random.randint(0, 18446744073709551615)
        fps = values['fps']

        model = ModelSamplingSD3.patch(unet, shift)[0]
        positive = CLIPTextEncode.encode(clip, positive_prompt)[0]
        negative = CLIPTextEncode.encode(clip, negative_prompt)[0]

        input_image = LoadImage.load_image(input_image_path)[0]
        clip_vision_output = CLIPVisionEncode.encode(clip_vision, input_image, crop)[0]
        positive, negative, out_latent = WanImageToVideo.encode(positive, negative, vae, width, height, length, batch_size, start_image=input_image, clip_vision_output=clip_vision_output)
        out_samples = KSampler.sample(model, seed, steps, cfg, sampler_name, scheduler, positive, negative, out_latent)[0]

        decoded_images = VAEDecode.decode(vae, out_samples)[0].detach()
        
        # Create output directory and save video locally
        os.makedirs("/content/ComfyUI/output", exist_ok=True)
        result = f"/content/ComfyUI/output/wan2.2-i2v-rapid-{seed}-local.mp4"
        images_to_mp4(decoded_images, result, fps)
        
        job_id = values.get('job_id', f'local-job-{seed}')
        
        # Calculate execution time
        execution_time = round(time.time() - start_time, 2)
        
        # Return local file path instead of upload URL with execution time
        return {
            "jobId": job_id,
            "result": result,
            "status": "DONE",
            "message": "Video saved locally",
            "execution_time": execution_time
        }
    except Exception as e:
        job_id = values.get('job_id', 'unknown-job') if 'values' in locals() else 'unknown-job'
        print(f"Error in generate: {str(e)}")
        execution_time = round(time.time() - start_time, 2)
        return {
            "jobId": job_id,
            "result": f"FAILED: {str(e)}",
            "status": "FAILED",
            "execution_time": execution_time
        }

runpod.serverless.start({"handler": generate})