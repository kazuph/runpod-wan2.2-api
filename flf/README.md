# FLF (First-Last Frame) Video Generation

## 問題と解決策

### 現在の問題
- ComfyUIが個別フレームを出力し、ホスト側でffmpegで結合している
- これは運用上非効率的

### 正しい解決策

#### 1. Dockerコンテナ内での完結処理

```dockerfile
# Dockerfile
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# ComfyUI + VideoHelperSuite インストール
RUN cd /comfyui/custom_nodes && \
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite
```

#### 2. ワークフローの修正

SaveImageノードの代わりにVHS_VideoCombineノードを使用：

```json
{
  "video_output": {
    "inputs": {
      "images": ["vae_decode", 0],
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "flf_output",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": true,
      "save_output": true
    },
    "class_type": "VHS_VideoCombine"
  }
}
```

#### 3. 運用フロー

1. **コンテナ内で完結**：
   - 画像アップロード → FLF処理 → 動画生成 → 動画ファイル出力
   - ffmpeg不要、すべてComfyUI内で処理

2. **出力**：
   - `/comfyui/output/flf_output_00001.mp4` として直接動画ファイルが生成

3. **ボリュームマウント**：
   ```yaml
   volumes:
     - ./output:/comfyui/output
   ```

## 実装手順

### 1. Dockerイメージのビルド

```bash
cd flf
docker compose build
```

### 2. コンテナの実行

```bash
docker compose up -d
```

### 3. APIでの使用

```python
# 直接動画が返される
response = requests.post("http://localhost:8081/run", json={
    "input": {
        "start_image": "girl1.jpg",
        "end_image": "girl2.jpg",
        "output_format": "mp4"  # 動画として出力
    }
})
```

## メリット

1. **効率的**: フレーム→動画変換がコンテナ内で完結
2. **シンプル**: ffmpeg不要
3. **高速**: ディスクI/O削減
4. **スケーラブル**: RunPodで複数インスタンス展開可能

## 現在の暫定対応

VHS_VideoCombineノードが利用できない場合、コンテナ内でffmpegを実行：

```python
# worker内で直接変換
import subprocess

def frames_to_video(frames, output_path):
    # コンテナ内でffmpeg実行
    subprocess.run([
        "ffmpeg", "-framerate", "24",
        "-pattern_type", "sequence",
        "-i", f"{frame_pattern}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        output_path
    ])
    
    # base64エンコードして返す
    with open(output_path, 'rb') as f:
        return base64.b64encode(f.read()).decode()
```

これにより、APIレスポンスとして直接動画データが返されます。