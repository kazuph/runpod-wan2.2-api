#!/usr/bin/env python3
"""
Fix attention import in model.py - use correct function
"""
import re

def fix_attention_import():
    file_path = "/content/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper/comfy_wanvideo/wanvideo/modules/model.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Fix the attention import - use optimized_attention instead
        content = re.sub(
            r'from comfy\.ldm\.modules\.attention import attention',
            'from comfy.ldm.modules.attention import optimized_attention as attention',
            content
        )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✓ Fixed attention import to use optimized_attention")
        
    except Exception as e:
        print(f"✗ Failed to fix attention import: {e}")

if __name__ == "__main__":
    fix_attention_import()