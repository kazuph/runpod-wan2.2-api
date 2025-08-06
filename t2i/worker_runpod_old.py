import os, json, requests, random, time, runpod
from PIL import Image
import sys
sys.path.append('/content/ComfyUI')

import torch
import numpy as np

# Import ComfyUI and load custom nodes properly
from comfy import model_management
from nodes import NODE_CLASS_MAPPINGS

# Force import custom nodes
import importlib
import folder_paths

# Get custom nodes path and load ComfyUI-WanVideoWrapper properly
import importlib.util

custom_node_paths = folder_paths.get_folder_paths("custom_nodes")
for custom_node_path in custom_node_paths:
    # Load ComfyUI-WanVideoWrapper
    wan_path = os.path.join(custom_node_path, "ComfyUI-WanVideoWrapper")
    if os.path.exists(wan_path):
        # Add the WanVideoWrapper path to sys.path for relative imports
        sys.path.insert(0, wan_path)
        
        try:
            # Load the __init__.py file as a proper module
            init_path = os.path.join(wan_path, "__init__.py")
            spec = importlib.util.spec_from_file_location("ComfyUI_WanVideoWrapper", init_path)
            wan_module = importlib.util.module_from_spec(spec)
            
            # Register the module in sys.modules so relative imports work
            sys.modules["ComfyUI_WanVideoWrapper"] = wan_module
            
            # Execute the module to load all nodes
            spec.loader.exec_module(wan_module)
            
            # Get the NODE_CLASS_MAPPINGS from the loaded module
            if hasattr(wan_module, "NODE_CLASS_MAPPINGS"):
                NODE_CLASS_MAPPINGS.update(wan_module.NODE_CLASS_MAPPINGS)
                print(f"Loaded {len(wan_module.NODE_CLASS_MAPPINGS)} WanVideo nodes from package")
            else:
                print("WanVideoWrapper package loaded but no NODE_CLASS_MAPPINGS found")
                
        except Exception as e:
            print(f"Failed to load WanVideo package: {e}")
            import traceback
            traceback.print_exc()

# Check what nodes we have
wan_nodes = [k for k in NODE_CLASS_MAPPINGS.keys() if 'WanVideo' in k]
print(f"Available WanVideo nodes: {wan_nodes}")

# Initialize nodes (only if available)
if "LoadWanVideoT5TextEncoder" in NODE_CLASS_MAPPINGS:
    LoadWanVideoT5TextEncoder = NODE_CLASS_MAPPINGS["LoadWanVideoT5TextEncoder"]()
    WanVideoModelLoader = NODE_CLASS_MAPPINGS["WanVideoModelLoader"]()
    WanVideoTextEncode = NODE_CLASS_MAPPINGS["WanVideoTextEncode"]()
    WanVideoSampler = NODE_CLASS_MAPPINGS["WanVideoSampler"]()
    WanVideoDecode = NODE_CLASS_MAPPINGS["WanVideoDecode"]()
    WanVideoVACEEncode = NODE_CLASS_MAPPINGS["WanVideoVACEEncode"]()
    SaveImage = NODE_CLASS_MAPPINGS["SaveImage"]()
    print("WanVideo nodes initialized")
    wan_nodes_available = True
else:
    print("WanVideo nodes not available - will use test mode")
    wan_nodes_available = False

# Load models if nodes are available
models_loaded = False
if wan_nodes_available:
    try:
        with torch.inference_mode():
            # Load text encoder
            text_encoder = LoadWanVideoT5TextEncoder.loadmodel(
                text_encoder="umt5-xxl-enc-bf16.safetensors",
                precision="fp16"
            )[0]
            
            # Load main model
            diffusion_model = WanVideoModelLoader.loadmodel(
                diffusion_model="Wan2_1-T2V-14B_fp8_e4m3fn.safetensors",
                precision="fp8_e4m3fn",
                attention_mode="sageattn"
            )[0]
            
            # Load VAE
            vae = WanVideoModelLoader.loadvae(
                vae="Wan2_1_VAE_bf16.safetensors",
                precision="bf16"
            )[0]
            
            # Load VACE module
            vace_module = WanVideoModelLoader.loadmodel(
                diffusion_model="Wan2_1-VACE_module_14B_fp8_e4m3fn.safetensors",
                precision="fp8_e4m3fn",
                attention_mode="sageattn"
            )[0]
            
            print("All WAN2.1 models loaded successfully")
            models_loaded = True
    except Exception as e:
        print(f"Failed to load models: {e}")
        models_loaded = False

# Load base workflow
workflow_path = '/content/ComfyUI/wan21_t2i_workflow.json'
if os.path.exists(workflow_path):
    with open(workflow_path, 'r') as f:
        BASE_WORKFLOW = json.load(f)
else:
    BASE_WORKFLOW = None

@torch.inference_mode()
def generate(input):
    """Generate T2I image using WAN2.1"""
    start_time = time.time()
    
    try:
        values = input["input"]
        
        # Get parameters
        positive_prompt = values.get('positive_prompt', 'A beautiful landscape')
        negative_prompt = values.get('negative_prompt', '')
        width = values.get('width', 576)
        height = values.get('height', 576)
        seed = values.get('seed', 0)
        if seed == 0:
            random.seed(int(time.time()))
            seed = random.randint(0, 18446744073709551615)
        
        steps = values.get('steps', 20)
        cfg = values.get('cfg', 7.0)
        
        print(f"Generating WAN2.1 T2I image")
        print(f"Prompt: {positive_prompt}")
        print(f"Resolution: {width}x{height}, Steps: {steps}, CFG: {cfg}, Seed: {seed}")
        
        if models_loaded:
            # Generate using WAN2.1 models
            result_path = generate_wan21_image(
                positive_prompt, negative_prompt,
                width, height, steps, cfg, seed
            )
            if result_path:
                message = "WAN2.1 T2I image generated successfully"
            else:
                result_path = generate_test_image(width, height, seed, positive_prompt)
                message = "Generated test image (WAN2.1 generation failed)"
        else:
            # Fallback to test image
            result_path = generate_test_image(width, height, seed, positive_prompt)
            message = "Generated test image (WAN2.1 models not loaded)"
        
        job_id = values.get('job_id', f'job-{seed}')
        execution_time = round(time.time() - start_time, 2)
        
        return {
            "jobId": job_id,
            "result": result_path,
            "status": "DONE",
            "message": message,
            "execution_time": execution_time,
            "parameters": {
                "prompt": positive_prompt,
                "negative": negative_prompt,
                "width": width,
                "height": height,
                "steps": steps,
                "cfg": cfg,
                "seed": seed
            }
        }
        
    except Exception as e:
        print(f"Error in generate: {str(e)}")
        import traceback
        traceback.print_exc()
        
        job_id = values.get('job_id', 'error-job') if 'values' in locals() else 'error-job'
        execution_time = round(time.time() - start_time, 2)
        
        return {
            "jobId": job_id,
            "result": f"FAILED: {str(e)}",
            "status": "FAILED",
            "execution_time": execution_time
        }

def generate_wan21_image(positive_prompt, negative_prompt, width, height, steps, cfg, seed):
    """Generate image using WAN2.1 models"""
    try:
        # Encode positive prompt
        positive_cond = WanVideoTextEncode.process(
            text_encoder,
            positive_prompt,
            force_offload=True
        )[0]
        
        # Encode negative prompt
        negative_cond = WanVideoTextEncode.process(
            text_encoder,
            negative_prompt if negative_prompt else "",
            force_offload=True
        )[0]
        
        # Apply VACE enhancement to positive conditioning
        positive_cond_vace = WanVideoVACEEncode.process(
            text_encoder,
            positive_cond,
            vace_module,
            vace_ratio=0.5,
            force_offload=True
        )[0]
        
        # Generate samples
        samples = WanVideoSampler.process(
            diffusion_model=diffusion_model,
            positive_cond=positive_cond_vace,
            negative_cond=negative_cond,
            video_length=1,  # Single frame for T2I
            height=height,
            width=width,
            base_resolution=512,
            seed=seed,
            steps=steps,
            cfg=cfg,
            cfg_start_percent=0.0,
            cfg_end_percent=1.0,
            noise_type="repeat_sequence",
            mixed_precision=True,
            optimize_vae_decode=False,
            sampler="dpmpp_2m_sde"
        )[0]
        
        # Decode to images
        images = WanVideoDecode.decode(
            vae,
            samples,
            seamless_tile=False
        )[0]
        
        # Save image
        filename_prefix = f"wan21_t2i_{seed}"
        saved = SaveImage.save_images(
            images,
            filename_prefix
        )
        
        # Get output path
        if saved and "ui" in saved and "images" in saved["ui"]:
            for img_info in saved["ui"]["images"]:
                if "filename" in img_info:
                    output_path = os.path.join("/content/ComfyUI/output", img_info["filename"])
                    if os.path.exists(output_path):
                        return output_path
        
        return None
        
    except Exception as e:
        print(f"WAN2.1 generation error: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_test_image(width, height, seed, prompt=""):
    """Generate a test gradient image"""
    img_array = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Create gradient
    for y in range(height):
        for x in range(width):
            img_array[y, x] = [
                int(255 * x / width),
                int(255 * y / height),
                128
            ]
    
    # Add some text
    from PIL import ImageDraw, ImageFont
    img = Image.fromarray(img_array, 'RGB')
    draw = ImageDraw.Draw(img)
    
    text_lines = [
        "WAN2.1 T2I Test Mode",
        f"Prompt: {prompt[:40]}...",
        f"Size: {width}x{height}",
        f"Seed: {seed}"
    ]
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    y_offset = 10
    for line in text_lines:
        draw.text((10, y_offset), line, fill=(255, 255, 255), font=font)
        y_offset += 20
    
    # Save image
    os.makedirs("/content/ComfyUI/output", exist_ok=True)
    result_path = f"/content/ComfyUI/output/test_{seed}.png"
    img.save(result_path, 'PNG')
    
    print(f"Test image saved to: {result_path}")
    return result_path

print("Starting RunPod server on port 8083...")
print(f"WAN2.1 T2I API - Models loaded: {models_loaded}")
runpod.serverless.start({"handler": generate})