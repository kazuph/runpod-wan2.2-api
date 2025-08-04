#!/usr/bin/env python3
"""
Check image dimensions and calculate appropriate video aspect ratio
"""
from PIL import Image
import sys
import os

def get_image_info(image_path):
    """Get image dimensions and suggest video dimensions"""
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            aspect_ratio = width / height
            
            print(f"Image: {os.path.basename(image_path)}")
            print(f"Original size: {width}x{height}")
            print(f"Aspect ratio: {aspect_ratio:.3f}")
            
            # Suggest video dimensions based on aspect ratio
            if aspect_ratio > 1.5:  # Wide image
                video_width, video_height = 1024, 576  # 16:9-ish
                print("Suggested: Wide format (16:9)")
            elif aspect_ratio < 0.8:  # Tall image
                video_width, video_height = 576, 1024  # 9:16 (vertical)
                print("Suggested: Vertical format (9:16)")
            else:  # Square-ish
                video_width, video_height = 720, 720  # Square
                print("Suggested: Square format (1:1)")
                
            print(f"Video dimensions: {video_width}x{video_height}")
            print("-" * 40)
            
            return width, height, video_width, video_height, aspect_ratio
            
    except Exception as e:
        print(f"Error reading {image_path}: {e}")
        return None

if __name__ == "__main__":
    images = [
        "input/input_003.jpeg",
        "input/input_004.jpeg"
    ]
    
    for img_path in images:
        if os.path.exists(img_path):
            get_image_info(img_path)
        else:
            print(f"Image not found: {img_path}")