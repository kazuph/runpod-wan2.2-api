"""
WAN2.1 T2I workflow implementation using ComfyUI execution
"""
import json
import os
import sys
import uuid
import torch

sys.path.append('/content/ComfyUI')

# Import ComfyUI components
import execution
import folder_paths
from PIL import Image
import numpy as np

def create_t2i_workflow(positive_prompt, negative_prompt, width, height, steps, cfg, seed):
    """Create WAN2.1 T2I workflow"""
    workflow = {
        "1": {
            "class_type": "LoadWanVideoT5TextEncoder",
            "inputs": {
                "text_encoder": "umt5-xxl-enc-bf16.safetensors",
                "precision": "fp16_fixed"
            }
        },
        "2": {
            "class_type": "WanVideoModelLoader", 
            "inputs": {
                "diffusion_model": "Wan2_1-T2V-14B_fp8_e4m3fn.safetensors",
                "precision": "fp8_e4m3fn",
                "attention_mode": "sageattn"
            }
        },
        "3": {
            "class_type": "WanVideoModelLoader",
            "inputs": {
                "vae": "Wan2_1_VAE_bf16.safetensors",
                "precision": "bf16"
            }
        },
        "4": {
            "class_type": "WanVideoTextEncode",
            "inputs": {
                "text_encoder": ["1", 0],
                "text": positive_prompt,
                "force_offload": True
            }
        },
        "5": {
            "class_type": "WanVideoTextEncode",
            "inputs": {
                "text_encoder": ["1", 0],
                "text": negative_prompt,
                "force_offload": True
            }
        },
        "6": {
            "class_type": "WanVideoSampler",
            "inputs": {
                "diffusion_model": ["2", 0],
                "positive_cond": ["4", 0],
                "negative_cond": ["5", 0],
                "video_length": 1,  # Static image
                "height": height,
                "width": width,
                "base_resolution": 512,
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "cfg_start_percent": 0.0,
                "cfg_end_percent": 1.0,
                "noise_type": "repeat_sequence",
                "mixed_precision": True,
                "optimize_vae_decode": False,
                "sampler": "dpmpp_2m_sde"
            }
        },
        "7": {
            "class_type": "WanVideoDecode",
            "inputs": {
                "vae": ["3", 0],
                "samples": ["6", 0],
                "seamless_tile": False
            }
        },
        "8": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["7", 0],
                "filename_prefix": f"wan21_t2i_{seed}"
            }
        }
    }
    
    return workflow

def execute_workflow(workflow):
    """Execute the workflow using ComfyUI"""
    try:
        # Initialize prompt executor
        prompt_id = str(uuid.uuid4())
        
        # Create outputs dict
        outputs = {}
        
        # Execute workflow
        execution.PromptExecutor(server=None).execute(
            workflow,
            prompt_id,
            {"client_id": prompt_id},
            outputs
        )
        
        # Get output image path
        if "8" in outputs and outputs["8"]["images"]:
            return outputs["8"]["images"][0]["filename"]
        
        return None
        
    except Exception as e:
        print(f"Workflow execution error: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_t2i(positive_prompt, negative_prompt, width, height, steps, cfg, seed):
    """Generate T2I image using WAN2.1"""
    print(f"Creating WAN2.1 T2I workflow...")
    workflow = create_t2i_workflow(
        positive_prompt, negative_prompt,
        width, height, steps, cfg, seed
    )
    
    print(f"Executing workflow...")
    output_file = execute_workflow(workflow)
    
    if output_file:
        output_path = os.path.join(folder_paths.get_output_directory(), output_file)
        print(f"Image generated: {output_path}")
        return output_path
    else:
        print("Failed to generate image")
        return None

if __name__ == "__main__":
    # Test generation
    result = generate_t2i(
        positive_prompt="A beautiful mountain landscape",
        negative_prompt="blurry, low quality", 
        width=576,
        height=576,
        steps=20,
        cfg=7.0,
        seed=42
    )