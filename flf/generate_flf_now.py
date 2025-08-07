#!/usr/bin/env python3
"""
Generate FLF video NOW with different parameters
"""

import json
import requests
import time
import os
import random

COMFYUI_URL = "http://localhost:8188"

def upload_image(path):
    """Upload image to ComfyUI"""
    with open(path, 'rb') as f:
        files = {"image": (os.path.basename(path), f, "image/jpeg")}
        response = requests.post(f"{COMFYUI_URL}/upload/image", files=files)
        return response.json().get("name")

print("🎬 FLF動画生成開始！")
print("="*50)

# Check ComfyUI
try:
    response = requests.get(f"{COMFYUI_URL}/system_stats")
    print("✅ ComfyUI稼働中")
except:
    print("❌ ComfyUI not accessible")
    exit(1)

# Upload images - 異なる画像の組み合わせも試せます
print("📤 画像アップロード中...")
start_img = upload_image("/home/kazuph/runpod-wan2.2-api/rapid-i2v/input/girl2.jpg")  # 逆にしてみる
end_img = upload_image("/home/kazuph/runpod-wan2.2-api/rapid-i2v/input/girl1.jpg")

seed = random.randint(100, 999)
print(f"🎲 Seed: {seed}")

# FLF workflow with WanFirstLastFrameToVideo
workflow = {
    "1": {
        "inputs": {
            "ckpt_name": "wan2.2-i2v-rapid-aio.safetensors"
        },
        "class_type": "CheckpointLoaderSimple"
    },
    "2": {
        "inputs": {
            "image": start_img,
            "upload": "image"
        },
        "class_type": "LoadImage"
    },
    "3": {
        "inputs": {
            "image": end_img,
            "upload": "image"
        },
        "class_type": "LoadImage"
    },
    "4": {
        "inputs": {
            "text": "beautiful smooth morphing transition between two female faces, gradual transformation, cinematic quality, natural movement",
            "clip": ["1", 1]
        },
        "class_type": "CLIPTextEncode"
    },
    "5": {
        "inputs": {
            "text": "static, blurry, distortion, abrupt change, low quality, artifacts, mouth opening, talking",
            "clip": ["1", 1]
        },
        "class_type": "CLIPTextEncode"
    },
    "6": {
        "inputs": {
            "positive": ["4", 0],
            "negative": ["5", 0],
            "vae": ["1", 2],
            "start_image": ["2", 0],
            "end_image": ["3", 0],
            "width": 576,  # 少し大きく
            "height": 576,
            "length": 49,  # 約2秒
            "batch_size": 1
        },
        "class_type": "WanFirstLastFrameToVideo"
    },
    "7": {
        "inputs": {
            "model": ["1", 0],
            "positive": ["6", 0],
            "negative": ["6", 1],
            "latent_image": ["6", 2],
            "seed": seed,
            "steps": 8,  # もう少しステップを増やす
            "cfg": 2.0,  # CFGも調整
            "sampler_name": "lcm",
            "scheduler": "beta",
            "denoise": 1.0
        },
        "class_type": "KSampler"
    },
    "8": {
        "inputs": {
            "samples": ["7", 0],
            "vae": ["1", 2]
        },
        "class_type": "VAEDecode"
    },
    "9": {
        "inputs": {
            "images": ["8", 0],
            "filename_prefix": f"flf_morph_{seed}"
        },
        "class_type": "SaveImage"
    }
}

print("🚀 ワークフロー送信中...")
print(f"  解像度: 576x576")
print(f"  フレーム数: 49 (約2秒)")
print(f"  ステップ数: 8")

response = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
result = response.json()

prompt_id = result.get("prompt_id")
if not prompt_id:
    print(f"❌ Failed: {result}")
    exit(1)

print(f"📋 プロンプトID: {prompt_id}")
print("⏳ 処理中...")

# Wait for completion
start_time = time.time()
while time.time() - start_time < 120:  # 2分まで待つ
    history = requests.get(f"{COMFYUI_URL}/history/{prompt_id}").json()
    
    if prompt_id in history:
        if "outputs" in history[prompt_id]:
            elapsed = time.time()-start_time
            print(f"\n✅ 完了！処理時間: {elapsed:.1f}秒")
            
            outputs = history[prompt_id]["outputs"]
            images = []
            for node_id, output in outputs.items():
                if "images" in output:
                    for img in output["images"]:
                        images.append(img['filename'])
            
            if images:
                print(f"📹 生成フレーム数: {len(images)}")
                
                # Create video
                output_dir = "/home/kazuph/runpod-wan2.2-api/comfyui_workflow/output"
                video_output = f"/home/kazuph/runpod-wan2.2-api/flf/output/flf_morph_{seed}.mp4"
                
                # Use first image name pattern
                pattern = images[0].replace("00001", "%05d")
                
                cmd = f"ffmpeg -framerate 24 -pattern_type sequence -start_number 1 -i '{output_dir}/{pattern}' -c:v libx264 -pix_fmt yuv420p -crf 19 {video_output} -y 2>/dev/null"
                
                if os.system(cmd) == 0:
                    if os.path.exists(video_output):
                        size_kb = os.path.getsize(video_output) / 1024
                        print(f"\n🎉 動画生成成功！")
                        print(f"📍 場所: {video_output}")
                        print(f"📊 サイズ: {size_kb:.1f} KB")
                    else:
                        print(f"⚠️ 動画ファイルが見つかりません")
                else:
                    print(f"⚠️ ffmpeg変換に失敗")
            
            exit(0)
        
        if "status" in history[prompt_id]:
            status = history[prompt_id]["status"]
            if status.get("status_str") == "error":
                print(f"\n❌ Error: {status}")
                exit(1)
    
    print(".", end="", flush=True)
    time.sleep(2)

print("\n❌ タイムアウト")
exit(1)