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
    try:
        values = input["input"]

        input_image = values['input_image']
        input_image_path = get_input_image_path(input_image)
        positive_prompt = values['positive_prompt'] # Fashion magazine, dynamic blur, hand-held lens, a close-up photo, the scene of a group of 21-year-old goths at a warehouse party, with a movie-like texture, super-realistic effect, realism.
        negative_prompt = values['negative_prompt'] # 色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走
        crop = values['crop'] # center
        width = values['width'] # 1280
        height = values['height'] # 530
        length = values['length'] # 53
        batch_size = values['batch_size'] # 1
        shift = values['shift'] # 8.0
        cfg = values['cfg'] # 1.0
        sampler_name = values['sampler_name'] # lcm
        scheduler = values['scheduler'] # beta
        steps = values['steps'] # 4
        seed = values['seed'] # 0
        if seed == 0:
            random.seed(int(time.time()))
            seed = random.randint(0, 18446744073709551615)
        fps = values['fps'] # 24

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
        
        # Return local file path instead of upload URL
        return {"jobId": job_id, "result": result, "status": "DONE", "message": "Video saved locally"}
    except Exception as e:
        job_id = values.get('job_id', 'unknown-job') if 'values' in locals() else 'unknown-job'
        print(f"Error in generate: {str(e)}")
        return {"jobId": job_id, "result": f"FAILED: {str(e)}", "status": "FAILED"}

runpod.serverless.start({"handler": generate})