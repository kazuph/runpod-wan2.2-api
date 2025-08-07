#!/usr/bin/env python3
"""
Test proper FLF implementation with direct video output
"""

import requests
import json
import base64
import time
import os

def test_flf_proper():
    """Test FLF with proper container video output"""
    
    print("🎬 Testing Proper FLF Implementation")
    print("=" * 60)
    
    # Read test images and encode to base64
    with open("/home/kazuph/runpod-wan2.2-api/rapid-i2v/input/girl1.jpg", "rb") as f:
        start_image_b64 = base64.b64encode(f.read()).decode()
    
    with open("/home/kazuph/runpod-wan2.2-api/rapid-i2v/input/girl2.jpg", "rb") as f:
        end_image_b64 = base64.b64encode(f.read()).decode()
    
    # Prepare request
    payload = {
        "input": {
            "start_image": start_image_b64,
            "end_image": end_image_b64,
            "positive_prompt": "smooth morphing transition between two faces",
            "negative_prompt": "static, blurry, distortion",
            "width": 512,
            "height": 512,
            "length": 25,  # 1 second at 24fps
            "fps": 24,
            "seed": 42
        }
    }
    
    # Send request to container API
    api_url = "http://localhost:8081"
    
    print("📤 Sending request to FLF container...")
    print(f"  Resolution: 512x512")
    print(f"  Length: 25 frames (1 second)")
    
    try:
        start_time = time.time()
        response = requests.post(f"{api_url}/runsync", json=payload, timeout=180)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "success":
                print(f"\n✅ Success! Video generated in {elapsed:.1f} seconds")
                
                # Save video
                video_b64 = result.get("video")
                if video_b64:
                    video_data = base64.b64decode(video_b64)
                    output_path = "/home/kazuph/runpod-wan2.2-api/flf/output/proper_flf_test.mp4"
                    
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(video_data)
                    
                    file_size_kb = len(video_data) / 1024
                    print(f"📹 Video saved: {output_path}")
                    print(f"📊 Size: {file_size_kb:.1f} KB")
                    print(f"🎯 Note: {result.get('note', 'Direct video output')}")
                    
                    return True
                else:
                    print("❌ No video data in response")
                    return False
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout (3 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_flf_proper()
    exit(0 if success else 1)