#!/usr/bin/env python3
"""
Fix attention import in model.py
"""
import re

def fix_attention_import():
    file_path = "/content/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper/comfy_wanvideo/wanvideo/modules/model.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Fix the attention import
        # Change from comfy_wanvideo.attention to comfy's attention
        content = re.sub(
            r'from comfy_wanvideo\.attention import attention',
            'from comfy.ldm.modules.attention import attention',
            content
        )
        
        # Alternative fix if the above doesn't work
        if 'from comfy.ldm.modules.attention import attention' not in content:
            # Try using pytorch's attention directly
            content = re.sub(
                r'from comfy_wanvideo\.attention import attention',
                '# Attention import removed - using PyTorch native attention',
                content
            )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✓ Fixed attention import in model.py")
        
    except Exception as e:
        print(f"✗ Failed to fix attention import: {e}")

if __name__ == "__main__":
    fix_attention_import()