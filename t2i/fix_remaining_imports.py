#!/usr/bin/env python3
"""
Fix remaining import issues in ComfyUI-WanVideoWrapper
"""
import os
import re

def fix_remaining_imports():
    """Fix remaining problematic imports"""
    base_path = "/content/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper/comfy_wanvideo"
    
    problematic_files = [
        "fantasytalking/nodes.py",
        "wanvideo/modules/__init__.py"
    ]
    
    for rel_path in problematic_files:
        file_path = os.path.join(base_path, rel_path)
        if os.path.exists(file_path):
            fix_file_imports(file_path)

def fix_file_imports(file_path):
    """Fix imports in a specific file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Fix the specific problematic imports
        # Pattern 1: from comfy_wanvideo.model import WanModel
        content = re.sub(
            r'from comfy_wanvideo\.model import',
            'from comfy_wanvideo.wanvideo.modules.model import',
            content
        )
        
        # Pattern 2: from comfy_wanvideo.wanvideo.model import 
        content = re.sub(
            r'from comfy_wanvideo\.wanvideo\.model import',
            'from comfy_wanvideo.wanvideo.modules.model import',
            content
        )
        
        # Pattern 3: import comfy_wanvideo.model
        content = re.sub(
            r'import comfy_wanvideo\.model',
            'import comfy_wanvideo.wanvideo.modules.model',
            content
        )
        
        # Pattern 4: import comfy_wanvideo.wanvideo.model
        content = re.sub(
            r'import comfy_wanvideo\.wanvideo\.model',
            'import comfy_wanvideo.wanvideo.modules.model',
            content
        )
        
        # Fix relative imports that might be missed
        content = re.sub(
            r'from \.model import',
            'from .modules.model import',
            content
        )
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✓ Fixed imports in: {file_path}")
        else:
            print(f"- No changes needed in: {file_path}")
            
    except Exception as e:
        print(f"✗ Could not fix imports in {file_path}: {e}")

if __name__ == "__main__":
    fix_remaining_imports()