#!/usr/bin/env python3
"""
Working FLF Test
"""
import requests
import json
import time

# Test working FLF
url = "http://127.0.0.1:8081/runsync"

# Simple 1x1 pixel images
start_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA60e6kgAAAABJRU5ErkJggg=="  # red
end_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwAChAGA60e6kgAAAABJRU5ErkJggg=="    # blue

payload = {
    "input": {
        "start_image": start_image,
        "end_image": end_image,
        "positive_prompt": "smooth transition",
        "negative_prompt": "static",
        "width": 512,
        "height": 512, 
        "length": 25,
        "fps": 24
    }
}

print("🎬 Testing FLF Generation")
print("=" * 50)

start_time = time.time()
response = requests.post(url, json=payload, timeout=120)

if response.status_code == 200:
    result = response.json()
    print(f"Status: {result.get('status')}")
    
    if result.get('status') == 'COMPLETED':
        if 'video' in result:
            print(f"✅ FLF VIDEO GENERATED!")
            print(f"Video size: {len(result['video'])} chars (base64)")
            print(f"Time: {time.time() - start_time:.1f}s")
        else:
            print(f"✅ FRAMES GENERATED!")
            print(f"Time: {time.time() - start_time:.1f}s")
    else:
        print(f"❌ Failed: {result.get('error')}")
else:
    print(f"❌ HTTP Error: {response.status_code}")
    print(response.text)