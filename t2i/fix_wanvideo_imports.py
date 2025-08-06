#!/usr/bin/env python3
"""
Fix ComfyUI-WanVideoWrapper import issues based on dr command recommendations.
This script restructures the package to avoid module name collisions.
"""
import os
import shutil
import re

def fix_wanvideo_imports():
    """Apply fixes to ComfyUI-WanVideoWrapper to resolve import issues."""
    
    base_path = "/content/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper"
    
    # Check if the directory exists
    if not os.path.exists(base_path):
        print(f"Error: {base_path} does not exist")
        return False
    
    # 1. Create a unique package structure
    print("1. Creating unique package structure...")
    comfy_wanvideo_path = os.path.join(base_path, "comfy_wanvideo")
    
    # If comfy_wanvideo already exists, skip restructuring
    if not os.path.exists(comfy_wanvideo_path):
        os.makedirs(comfy_wanvideo_path, exist_ok=True)
        
        # Move nodes.py to comfy_wanvideo/nodes.py
        nodes_src = os.path.join(base_path, "nodes.py")
        nodes_dst = os.path.join(comfy_wanvideo_path, "nodes.py")
        if os.path.exists(nodes_src):
            shutil.move(nodes_src, nodes_dst)
            print(f"  Moved nodes.py to comfy_wanvideo/nodes.py")
        
        # Move other Python files to comfy_wanvideo
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if item.endswith('.py') and item != '__init__.py' and os.path.isfile(item_path):
                dst_path = os.path.join(comfy_wanvideo_path, item)
                shutil.move(item_path, dst_path)
                print(f"  Moved {item} to comfy_wanvideo/{item}")
        
        # Move subdirectories (except comfy_wanvideo itself)
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path) and item not in ['comfy_wanvideo', '.git', '__pycache__']:
                dst_path = os.path.join(comfy_wanvideo_path, item)
                shutil.move(item_path, dst_path)
                print(f"  Moved directory {item} to comfy_wanvideo/{item}")
    
    # 2. Create/update comfy_wanvideo/__init__.py
    print("2. Creating comfy_wanvideo/__init__.py...")
    comfy_init_path = os.path.join(comfy_wanvideo_path, "__init__.py")
    with open(comfy_init_path, 'w') as f:
        f.write("""# ComfyUI WanVideo Wrapper Package
from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
""")
    
    # 3. Create/update top-level __init__.py
    print("3. Creating top-level __init__.py...")
    top_init_path = os.path.join(base_path, "__init__.py")
    with open(top_init_path, 'w') as f:
        f.write("""# ComfyUI-WanVideoWrapper - Top level package
from .comfy_wanvideo import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
""")
    
    # 4. Fix relative imports in all Python files
    print("4. Fixing relative imports...")
    for root, dirs, files in os.walk(comfy_wanvideo_path):
        # Skip __pycache__ directories
        if '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                fix_file_imports(file_path, comfy_wanvideo_path)
    
    print("5. Creating import test script...")
    test_script_path = os.path.join(base_path, "test_import.py")
    with open(test_script_path, 'w') as f:
        f.write("""#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from comfy_wanvideo.nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
    print(f"✓ Successfully imported {len(NODE_CLASS_MAPPINGS)} WanVideo nodes")
    print(f"✓ Node names: {list(NODE_CLASS_MAPPINGS.keys())[:5]}...")
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
""")
    os.chmod(test_script_path, 0o755)
    
    print("\nFixes applied successfully!")
    print(f"Test with: python {test_script_path}")
    return True

def fix_file_imports(file_path, package_root):
    """Fix relative imports in a Python file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Get relative path from package root
        rel_path = os.path.relpath(os.path.dirname(file_path), package_root)
        
        # Fix relative imports to use absolute imports from comfy_wanvideo
        # Pattern 1: from . import something
        content = re.sub(
            r'from\s+\.\s+import\s+',
            'from comfy_wanvideo import ',
            content
        )
        
        # Pattern 2: from .module import something
        content = re.sub(
            r'from\s+\.(\w+)\s+import\s+',
            r'from comfy_wanvideo.\1 import ',
            content
        )
        
        # Pattern 3: from ..module import something (parent imports)
        content = re.sub(
            r'from\s+\.\.(\w+)\s+import\s+',
            r'from comfy_wanvideo.\1 import ',
            content
        )
        
        # Fix imports of wanvideo.modules to comfy_wanvideo.wanvideo.modules
        content = re.sub(
            r'from\s+wanvideo\.modules\s+import\s+',
            'from comfy_wanvideo.wanvideo.modules import ',
            content
        )
        
        content = re.sub(
            r'import\s+wanvideo\.modules',
            'import comfy_wanvideo.wanvideo.modules',
            content
        )
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"  Fixed imports in: {os.path.relpath(file_path, package_root)}")
            
    except Exception as e:
        print(f"  Warning: Could not fix imports in {file_path}: {e}")

if __name__ == "__main__":
    fix_wanvideo_imports()