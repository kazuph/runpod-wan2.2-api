#!/usr/bin/env python3
"""
Initialize ComfyUI environment and verify WanVideo nodes are available
"""
import sys
import os

# Set ComfyUI path
sys.path.insert(0, '/content/ComfyUI')
os.chdir('/content/ComfyUI')

# Import ComfyUI modules in correct order
print("Initializing ComfyUI...")
import folder_paths
folder_paths.base_path = '/content/ComfyUI'
folder_paths.models_dir = '/content/ComfyUI/models'

# Load all custom nodes
import nodes
nodes.init_extra_nodes()

# Check if WanVideo nodes are loaded
from nodes import NODE_CLASS_MAPPINGS

wan_nodes = [k for k in NODE_CLASS_MAPPINGS.keys() if 'WanVideo' in k]
print(f"\nTotal nodes loaded: {len(NODE_CLASS_MAPPINGS)}")
print(f"WanVideo nodes found: {len(wan_nodes)}")

if wan_nodes:
    print("\nAvailable WanVideo nodes:")
    for node in sorted(wan_nodes):
        print(f"  - {node}")
else:
    print("\nWARNING: No WanVideo nodes found!")
    print("Checking custom nodes directory...")
    custom_nodes_dir = "/content/ComfyUI/custom_nodes"
    if os.path.exists(custom_nodes_dir):
        for item in os.listdir(custom_nodes_dir):
            print(f"  - {item}")

# Test loading specific nodes
try:
    if "LoadWanVideoT5TextEncoder" in NODE_CLASS_MAPPINGS:
        print("\n✓ LoadWanVideoT5TextEncoder is available")
    if "WanVideoModelLoader" in NODE_CLASS_MAPPINGS:
        print("✓ WanVideoModelLoader is available")
    if "WanVideoSampler" in NODE_CLASS_MAPPINGS:
        print("✓ WanVideoSampler is available")
except Exception as e:
    print(f"\nError checking nodes: {e}")

print("\nComfyUI initialization complete!")