#!/usr/bin/env python3
"""
Fix t5 import in __init__.py
"""
import re

def fix_t5_import():
    file_path = "/content/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper/comfy_wanvideo/wanvideo/modules/__init__.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Fix the t5 import path
        content = re.sub(
            r'from comfy_wanvideo\.t5 import',
            'from comfy_wanvideo.wanvideo.modules.t5 import',
            content
        )
        
        # Also fix if it's trying from .t5
        content = re.sub(
            r'from \.t5 import',
            'from .t5 import',
            content
        )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✓ Fixed t5 import in modules/__init__.py")
        
    except Exception as e:
        print(f"✗ Failed to fix t5 import: {e}")

if __name__ == "__main__":
    fix_t5_import()