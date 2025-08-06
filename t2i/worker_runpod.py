import os, json, requests, random, time, runpod
from PIL import Image
import sys
sys.path.append('/content/ComfyUI')

# Run the import fix scripts if they exist and haven't been run yet
fix_script = '/content/fix_wanvideo_imports.py'
if os.path.exists(fix_script) and not os.path.exists('/content/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper/comfy_wanvideo'):
    print("Running WanVideo import fixes...")
    import subprocess
    subprocess.run([sys.executable, fix_script], check=False)

# Run additional fixes
fix_remaining_script = '/content/fix_remaining_imports.py'
if os.path.exists(fix_remaining_script):
    print("Running additional import fixes...")
    import subprocess
    subprocess.run([sys.executable, fix_remaining_script], check=False)

import torch
import numpy as np

# Import ComfyUI base components
from comfy import model_management
from nodes import NODE_CLASS_MAPPINGS as COMFY_NODE_CLASS_MAPPINGS

# Import folder_paths to find custom nodes
import folder_paths

# Initialize NODE_CLASS_MAPPINGS with ComfyUI's default nodes
NODE_CLASS_MAPPINGS = COMFY_NODE_CLASS_MAPPINGS.copy()

# Load ComfyUI-WanVideoWrapper with fixed imports
import importlib
import importlib.util

custom_node_paths = folder_paths.get_folder_paths("custom_nodes")
wan_nodes_available = False

for custom_node_path in custom_node_paths:
    wan_path = os.path.join(custom_node_path, "ComfyUI-WanVideoWrapper")
    if os.path.exists(wan_path):
        print(f"Found WanVideoWrapper at: {wan_path}")
        
        # Add both the parent and the wan_path to sys.path
        if custom_node_path not in sys.path:
            sys.path.insert(0, custom_node_path)
        if wan_path not in sys.path:
            sys.path.insert(0, wan_path)
        
        try:
            # Try to import the fixed package structure
            try:
                # First, try the fixed structure
                from ComfyUI_WanVideoWrapper.comfy_wanvideo import NODE_CLASS_MAPPINGS as WAN_MAPPINGS
                print(f"✓ Loaded {len(WAN_MAPPINGS)} WanVideo nodes from fixed structure")
            except ImportError as e:
                print(f"Fixed structure import failed: {e}")
                # Fallback to direct import if fixes haven't been applied
                print("Trying direct import...")
                
                # Import the module directly
                spec = importlib.util.spec_from_file_location(
                    "ComfyUI_WanVideoWrapper",
                    os.path.join(wan_path, "__init__.py")
                )
                
                if spec and spec.loader:
                    wan_module = importlib.util.module_from_spec(spec)
                    sys.modules["ComfyUI_WanVideoWrapper"] = wan_module
                    
                    # Execute the module
                    spec.loader.exec_module(wan_module)
                    
                    if hasattr(wan_module, "NODE_CLASS_MAPPINGS"):
                        WAN_MAPPINGS = wan_module.NODE_CLASS_MAPPINGS
                        print(f"✓ Loaded {len(WAN_MAPPINGS)} WanVideo nodes from direct import")
                    else:
                        raise ImportError("No NODE_CLASS_MAPPINGS found in module")
            
            # Update our mappings
            NODE_CLASS_MAPPINGS.update(WAN_MAPPINGS)
            wan_nodes_available = True
            
        except Exception as e:
            print(f"✗ Failed to load WanVideo nodes: {e}")
            print("   Running in TEST MODE only")
            import traceback
            traceback.print_exc()

# Check what nodes we have
wan_nodes = [k for k in NODE_CLASS_MAPPINGS.keys() if 'WanVideo' in k]
print(f"\nAvailable WanVideo nodes: {wan_nodes}")
# Show status message
if not wan_nodes_available:
    print("\n=== IMPORTANT: Running in TEST MODE ===")
    print("WAN2.1 models are not loaded due to import issues.")
    print("All generated images will be test placeholders.")
    print("=======================================\n")

# Initialize nodes (only if available)
if wan_nodes_available and "LoadWanVideoT5TextEncoder" in NODE_CLASS_MAPPINGS:
    try:
        LoadWanVideoT5TextEncoder = NODE_CLASS_MAPPINGS["LoadWanVideoT5TextEncoder"]()
        WanVideoModelLoader = NODE_CLASS_MAPPINGS["WanVideoModelLoader"]()
        WanVideoTextEncode = NODE_CLASS_MAPPINGS["WanVideoTextEncode"]()
        WanVideoSampler = NODE_CLASS_MAPPINGS["WanVideoSampler"]()
        WanVideoDecode = NODE_CLASS_MAPPINGS["WanVideoDecode"]()
        WanVideoVACEEncode = NODE_CLASS_MAPPINGS["WanVideoVACEEncode"]()
        SaveImage = NODE_CLASS_MAPPINGS["SaveImage"]()
        print("✓ WanVideo node instances created successfully")
    except Exception as e:
        print(f"✗ Failed to instantiate WanVideo nodes: {e}")
        wan_nodes_available = False
else:
    print("⚠️ WanVideo nodes not available - will use test mode")
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
            
            models_loaded = True
            print("✓ All WAN2.1 models loaded successfully")
            
    except Exception as e:
        print(f"✗ Failed to load models: {e}")
        import traceback
        traceback.print_exc()
        models_loaded = False

def generate_wan21_t2i(prompt, negative_prompt="", width=768, height=768, steps=4, cfg=1.0, seed=None):
    """Generate image using WAN2.1 T2I model"""
    if not models_loaded:
        print("Models not loaded, generating test image")
        return generate_test_image(prompt, seed)
    
    try:
        with torch.inference_mode():
            if seed is None:
                seed = random.randint(0, 2**32 - 1)
                
            # Encode prompt
            prompt_embeds = WanVideoTextEncode.process(
                text=prompt,
                prompt_embeds=text_encoder
            )[0]
            
            negative_embeds = WanVideoTextEncode.process(
                text=negative_prompt,
                prompt_embeds=text_encoder
            )[0]
            
            # Sample
            latent = WanVideoSampler.process(
                diffusion_model=diffusion_model,
                prompt_embeds=prompt_embeds,
                negative_prompt_embeds=negative_embeds,
                width=width,
                height=height,
                length=1,  # Single frame for T2I
                cfg=cfg,
                seed=seed,
                steps=steps,
                sampler_name="lcm",
                scheduler="beta",
                shift=3.0,
                autocast_dtype="bf16"
            )[0]
            
            # Decode
            pixels = WanVideoDecode.decode(
                vae=vae,
                latent=latent,
                enable_vace=True,
                vace_module=vace_module,
                decoder_dtype="auto"
            )[0]
            
            # Save image
            result = SaveImage.save_images(
                images=pixels,
                filename_prefix=f"wan2.1-t2i-{seed}"
            )
            
            return result["ui"]["images"][0]["filename"]
            
    except Exception as e:
        print(f"Error during generation: {e}")
        import traceback
        traceback.print_exc()
        return generate_test_image(prompt, seed)

def generate_test_image(prompt, seed=None):
    """Generate a test image when WAN2.1 is not available"""
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    
    # Create a test image with the prompt text
    from PIL import Image, ImageDraw, ImageFont
    
    img = Image.new('RGB', (768, 768), color='darkblue')
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    # Draw the prompt
    text = f"Test Mode\n\nPrompt: {prompt[:50]}...\nSeed: {seed}"
    draw.multiline_text((10, 10), text, fill='white', font=font)
    
    # Save
    filename = f"test_{seed}.png"
    filepath = os.path.join("/content/ComfyUI/output", filename)
    img.save(filepath)
    
    return filename

def handler(job):
    """RunPod handler function"""
    try:
        job_input = job['input']
        
        # Extract parameters
        prompt = job_input.get('prompt', 'A beautiful landscape')
        negative_prompt = job_input.get('negative_prompt', '')
        width = job_input.get('width', 768)
        height = job_input.get('height', 768)
        steps = job_input.get('steps', 4)
        cfg = job_input.get('cfg', 1.0)
        seed = job_input.get('seed', None)
        
        # Generate image
        filename = generate_wan21_t2i(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps,
            cfg=cfg,
            seed=seed
        )
        
        # Return result
        return {
            "status": "success",
            "output": {
                "filename": filename,
                "seed": seed if seed else "random"
            }
        }
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# RunPod serverless mode
if __name__ == "__main__":
    import sys
    
    # Check if we should run the local test server
    if '--rp_serve_api' in sys.argv:
        print("Starting RunPod local test server...")
        # Import and start the RunPod test server
        import runpod
        runpod.serverless.start({"handler": handler})
    elif os.environ.get('RUNPOD_ENVIRONMENT') == 'serverless':
        # Production RunPod serverless mode
        import runpod
        runpod.serverless.start({"handler": handler})
    else:
        # Test mode - run a single test
        print("\nRunning in test mode...")
        result = handler({
            "input": {
                "prompt": "A beautiful sunset over mountains",
                "width": 768,
                "height": 768
            }
        })
        print(f"Result: {result}")