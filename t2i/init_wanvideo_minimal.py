#!/usr/bin/env python3
"""
Minimal initialization for WanVideo nodes.
This script attempts to load only the essential nodes for T2I generation.
"""
import sys
import os

# Add paths
sys.path.append('/content/ComfyUI')
sys.path.append('/content/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper')

# Import ComfyUI base
from comfy import model_management
from nodes import NODE_CLASS_MAPPINGS

# Try to load individual nodes directly
try:
    # Import the modules directory directly
    sys.path.append('/content/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper/comfy_wanvideo/wanvideo/modules')
    
    # Try importing model components
    try:
        from model import WanModel, rope_params
        print("✓ Loaded WanModel components")
    except Exception as e:
        print(f"✗ Failed to load model components: {e}")
    
    # Try to manually create essential nodes
    class LoadWanVideoT5TextEncoder:
        @classmethod
        def INPUT_TYPES(s):
            return {"required": {
                "text_encoder": (["umt5-xxl-enc-bf16.safetensors"],),
                "precision": (["fp16", "bf16"],)
            }}
        
        RETURN_TYPES = ("TEXT_ENCODER",)
        FUNCTION = "loadmodel"
        CATEGORY = "WanVideo"
        
        def loadmodel(self, text_encoder, precision):
            # Placeholder implementation
            print(f"Loading text encoder: {text_encoder} with precision: {precision}")
            return (None,)
    
    class WanVideoModelLoader:
        @classmethod
        def INPUT_TYPES(s):
            return {"required": {
                "diffusion_model": (["Wan2_1-T2V-14B_fp8_e4m3fn.safetensors"],),
                "precision": (["fp8_e4m3fn", "fp16", "bf16"],),
                "attention_mode": (["sageattn", "xformers"],)
            }}
        
        RETURN_TYPES = ("MODEL",)
        FUNCTION = "loadmodel"
        CATEGORY = "WanVideo"
        
        def loadmodel(self, diffusion_model, precision, attention_mode):
            # Placeholder implementation
            print(f"Loading model: {diffusion_model} with precision: {precision}")
            return (None,)
        
        @classmethod
        def loadvae(cls, vae, precision):
            # Placeholder implementation
            print(f"Loading VAE: {vae} with precision: {precision}")
            return (None,)
    
    # Register minimal nodes
    NODE_CLASS_MAPPINGS["LoadWanVideoT5TextEncoder"] = LoadWanVideoT5TextEncoder
    NODE_CLASS_MAPPINGS["WanVideoModelLoader"] = WanVideoModelLoader
    
    print("✓ Registered minimal WanVideo nodes")
    
except Exception as e:
    print(f"✗ Failed to initialize minimal WanVideo nodes: {e}")
    import traceback
    traceback.print_exc()

# List available nodes
wan_nodes = [k for k in NODE_CLASS_MAPPINGS.keys() if 'WanVideo' in k]
print(f"Available WanVideo nodes: {wan_nodes}")