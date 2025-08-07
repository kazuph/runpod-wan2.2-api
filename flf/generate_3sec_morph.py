#!/usr/bin/env python3
"""
3秒のゆっくりとした別人への変化動画を生成
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

print("🎬 3秒間の人物変化動画生成")
print("="*60)

# Check ComfyUI
try:
    response = requests.get(f"{COMFYUI_URL}/system_stats")
    print("✅ ComfyUI稼働中")
except:
    print("❌ ComfyUI not accessible")
    exit(1)

# Upload images
print("📤 画像アップロード中...")
start_img = upload_image("/home/kazuph/runpod-wan2.2-api/rapid-i2v/input/girl1.jpg")
end_img = upload_image("/home/kazuph/runpod-wan2.2-api/rapid-i2v/input/girl2.jpg")
print(f"  開始: {start_img}")
print(f"  終了: {end_img}")

seed = random.randint(1000, 9999)
print(f"🎲 Seed: {seed}")

# 3秒 = 72フレーム (24fps)
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
            "text": """Gradual metamorphosis from one person to completely different person over 3 seconds. 
            Slow facial feature transformation: eyes gradually changing shape and color, 
            nose reshaping smoothly, mouth and lips morphing to different form, 
            hair style and color transitioning naturally, skin tone shifting gradually,
            bone structure evolving, identity changing progressively frame by frame,
            seamless blend between two different individuals, cinematic quality morphing effect""",
            "clip": ["1", 1]
        },
        "class_type": "CLIPTextEncode"
    },
    "5": {
        "inputs": {
            "text": """static image, no change, sudden jump, instant transformation, 
            flickering, glitchy transition, unnatural morphing, distorted faces,
            blurry, low quality, artifacts, mouth opening, talking, lips moving""",
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
            "width": 576,  # 安定した解像度
            "height": 576,
            "length": 72,  # 3秒 (24fps × 3)
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
            "steps": 10,  # より多くのステップで品質向上
            "cfg": 2.5,  # プロンプトへの忠実度を上げる
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
            "filename_prefix": f"morph_3sec_{seed}"
        },
        "class_type": "SaveImage"
    }
}

print("\n🚀 ワークフロー送信中...")
print(f"  解像度: 576×576")
print(f"  長さ: 3秒 (72フレーム)")
print(f"  品質: 高 (10ステップ)")
print("  効果: ゆっくりとした人物変化")

response = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
result = response.json()

prompt_id = result.get("prompt_id")
if not prompt_id:
    print(f"❌ Failed: {result}")
    exit(1)

print(f"\n📋 プロンプトID: {prompt_id}")
print("⏳ 処理中（約1-2分かかります）...")

# Wait for completion
start_time = time.time()
dots = 0
while time.time() - start_time < 180:  # 3分まで待つ
    history = requests.get(f"{COMFYUI_URL}/history/{prompt_id}").json()
    
    if prompt_id in history:
        if "outputs" in history[prompt_id]:
            elapsed = time.time()-start_time
            print(f"\n\n✅ 生成完了！")
            print(f"⏱️ 処理時間: {elapsed:.1f}秒")
            
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
                video_output = f"/home/kazuph/runpod-wan2.2-api/flf/output/morph_3sec_{seed}.mp4"
                
                # Use first image name pattern
                pattern = images[0].replace("00001", "%05d")
                
                cmd = f"ffmpeg -framerate 24 -pattern_type sequence -start_number 1 -i '{output_dir}/{pattern}' -c:v libx264 -pix_fmt yuv420p -crf 19 {video_output} -y 2>/dev/null"
                
                if os.system(cmd) == 0:
                    if os.path.exists(video_output):
                        size_kb = os.path.getsize(video_output) / 1024
                        print(f"\n🎉 3秒モーフィング動画生成成功！")
                        print(f"📍 保存先: {video_output}")
                        print(f"📊 ファイルサイズ: {size_kb:.1f} KB")
                        print(f"🎬 内容: girl1からgirl2へ3秒かけてゆっくり変化")
                    else:
                        print(f"⚠️ 動画ファイルが見つかりません")
                else:
                    print(f"⚠️ ffmpeg変換に失敗しました")
                    print(f"フレームは生成されています: {output_dir}/{images[0]}")
            
            exit(0)
        
        if "status" in history[prompt_id]:
            status = history[prompt_id]["status"]
            if status.get("status_str") == "error":
                print(f"\n❌ Error: {status}")
                exit(1)
    
    # プログレス表示
    dots = (dots + 1) % 4
    progress = "." * dots + " " * (3 - dots)
    print(f"\r⏳ 処理中{progress} ({int(time.time()-start_time)}秒経過)", end="", flush=True)
    time.sleep(2)

print("\n❌ タイムアウト（3分経過）")
exit(1)