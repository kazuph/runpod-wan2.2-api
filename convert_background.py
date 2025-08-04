#!/usr/bin/env python3
"""
Convert PNG images with transparent background to white background
"""
from PIL import Image
import os

def convert_transparent_to_white(input_path, output_path):
    """Convert transparent background to white"""
    with Image.open(input_path) as img:
        # Create a white background image
        white_bg = Image.new('RGB', img.size, (255, 255, 255))
        
        # If image has transparency, paste it on white background
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            # Convert to RGBA if not already
            img = img.convert('RGBA')
            # Paste the image on white background using alpha channel as mask
            white_bg.paste(img, (0, 0), img)
        else:
            # No transparency, just convert to RGB
            white_bg = img.convert('RGB')
        
        # Save as PNG
        white_bg.save(output_path, 'PNG')
        print(f"Converted {input_path} -> {output_path}")

def convert_transparent_to_black(input_path, output_path):
    """Convert transparent background to black"""
    with Image.open(input_path) as img:
        # Create a black background image
        black_bg = Image.new('RGB', img.size, (0, 0, 0))
        
        # If image has transparency, paste it on black background
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            # Convert to RGBA if not already
            img = img.convert('RGBA')
            # Paste the image on black background using alpha channel as mask
            black_bg.paste(img, (0, 0), img)
        else:
            # No transparency, just convert to RGB
            black_bg = img.convert('RGB')
        
        # Save as PNG
        black_bg.save(output_path, 'PNG')
        print(f"Converted {input_path} -> {output_path}")

if __name__ == "__main__":
    # Convert input images to white background
    white_images = [
        ("input/input_001.png", "input/input_001_white.png"),
        ("input/input_002.png", "input/input_002_white.png")
    ]
    
    for input_path, output_path in white_images:
        if os.path.exists(input_path):
            convert_transparent_to_white(input_path, output_path)
        else:
            print(f"File not found: {input_path}")
    
    # Convert image_005 to black background for fireworks
    if os.path.exists("input/image_005.png"):
        convert_transparent_to_black("input/image_005.png", "input/image_005_black.png")
    else:
        print("File not found: input/image_005.png")
    
    # Convert image_006 to white background for happy video
    if os.path.exists("input/image_006.png"):
        convert_transparent_to_white("input/image_006.png", "input/image_006_white.png")
    else:
        print("File not found: input/image_006.png")
    
    # Convert new images to white background
    new_images = [
        ("input/image_007.png", "input/image_007_white.png"),
        ("input/image_008.png", "input/image_008_white.png"),
        ("input/image_009.png", "input/image_009_white.png"),
        ("input/image_010.png", "input/image_010_white.png"),
        ("input/image_011.png", "input/image_011_white.png")
    ]
    
    for input_path, output_path in new_images:
        if os.path.exists(input_path):
            convert_transparent_to_white(input_path, output_path)
        else:
            print(f"File not found: {input_path}")