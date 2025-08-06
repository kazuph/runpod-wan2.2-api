#!/usr/bin/env python3
"""
Fix tokenizers import in t5.py
"""
import re

def fix_tokenizers_import():
    file_path = "/content/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper/comfy_wanvideo/wanvideo/modules/t5.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Fix the tokenizers import path
        content = re.sub(
            r'from comfy_wanvideo\.tokenizers import',
            'from comfy_wanvideo.wanvideo.modules.tokenizers import',
            content
        )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✓ Fixed tokenizers import in t5.py")
        
    except Exception as e:
        print(f"✗ Failed to fix tokenizers import: {e}")

if __name__ == "__main__":
    fix_tokenizers_import()