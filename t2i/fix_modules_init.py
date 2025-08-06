#!/usr/bin/env python3
"""
Fix imports in modules/__init__.py
"""
import re

def fix_modules_init():
    file_path = "/content/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper/comfy_wanvideo/wanvideo/modules/__init__.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Fix the tokenizers import path
        content = re.sub(
            r'from comfy_wanvideo\.tokenizers import',
            'from .tokenizers import',
            content
        )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✓ Fixed tokenizers import in modules/__init__.py")
        
    except Exception as e:
        print(f"✗ Failed to fix modules/__init__.py: {e}")

if __name__ == "__main__":
    fix_modules_init()