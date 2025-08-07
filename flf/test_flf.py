#!/usr/bin/env python3
"""
Test script for FLF (First-Last Frame) video generation
"""

import os
import json
import requests
import time
import sys

def test_flf_generation():
    """Test FLF video generation with two images"""
    
    # Configuration
    api_url = "http://localhost:8081"
    
    # Test parameters
    test_params = {
        "input": {
            # Use girl1 and girl2 for smooth transition test
            "start_image": "girl1.jpg",
            "end_image": "girl2.jpg",
            "positive_prompt": "smooth morphing transition between two faces, gradual transformation, seamless blend",
            "negative_prompt": "static, blurry, low quality, mouth opening, talking, abrupt change, distortion",
            "width": 576,  # Safe resolution for testing
            "height": 576,
            "length": 49,  # Shorter for faster testing (~2 seconds)
            "batch_size": 1,
            "steps": 20,
            "cfg": 4.0,
            "seed": 42,
            "fps": 24
        }
    }
    
    print("🎬 Testing WAN2.2 FLF Video Generation")
    print("=" * 50)
    print(f"Start Image: {test_params['input']['start_image']}")
    print(f"End Image: {test_params['input']['end_image']}")
    print(f"Resolution: {test_params['input']['width']}x{test_params['input']['height']}")
    print(f"Length: {test_params['input']['length']} frames")
    print("=" * 50)
    
    # Check if API is running
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        print("✅ API server is running")
    except:
        print("⚠️  API server not responding, trying anyway...")
    
    # Submit job
    print("\nSubmitting FLF generation job...")
    try:
        response = requests.post(f"{api_url}/runsync", json=test_params, timeout=300)
        response.raise_for_status()
        result = response.json()
        
        print("\n✅ FLF Generation Complete!")
        print(f"Status: {result.get('status', 'UNKNOWN')}")
        
        if result.get('status') == 'success':
            print(f"Video saved to: {result.get('video_path', 'N/A')}")
            print(f"Seed used: {result.get('seed', 'N/A')}")
            print(f"Execution time: {result.get('execution_time', 'N/A')} seconds")
            
            # Check if output file exists
            output_path = result.get('video_path')
            if output_path and os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / 1024 / 1024
                print(f"File size: {file_size:.2f} MB")
                print("\n🎉 Test PASSED! FLF video generated successfully.")
                return True
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            print("\n❌ Test FAILED!")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ API Error: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_flf_generation()
    sys.exit(0 if success else 1)