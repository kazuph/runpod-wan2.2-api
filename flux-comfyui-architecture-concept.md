# Flux + ComfyUI + RunPod Worker アーキテクチャ詳細仕様書

## 1. システム概要

このプロジェクトは、AI画像生成モデル（Flux、Stable Diffusion等）をComfyUIのワークフローシステムとRunPodのサーバーレスワーカーインフラストラクチャを組み合わせて、スケーラブルな画像生成APIサービスを構築するものです。

### 主要技術スタック
- **ComfyUI**: ノードベースの画像生成ワークフローエンジン
- **RunPod**: サーバーレスGPUコンピューティングプラットフォーム
- **Docker**: コンテナ化技術による環境の統一
- **FastAPI/Uvicorn**: ローカルテスト用APIサーバー

## 2. Dockerコンテナアーキテクチャ

### 2.1 マルチステージビルド構造

Dockerfileは以下の4つのステージで構成されています：

```dockerfile
# Stage 1: Base image with common dependencies
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04 as base
- CUDA/cuDNN環境のセットアップ
- Python 3.10、Git、Wgetのインストール
- ComfyUIのクローンと依存関係のインストール
- RunPodライブラリのインストール

# Stage 2: Download models  
FROM base as downloader
- MODEL_TYPE引数に基づく動的なモデルダウンロード
- 各モデルタイプ（flux1-schnell、sdxl、sd3等）に応じたファイル取得

# Stage 3: Faceswap integration
FROM kazuph/runpod-faceswap-api:1.1.0 as faceswap
- 顔交換機能用の既存イメージを基盤として使用
- ComfyUIとモデルファイルのコピー

# Stage 4: Final image
FROM comfy as final
- 実行スクリプトとワークフローファイルの配置
- エントリーポイントの設定
```

### 2.2 Docker Compose設定

`docker-compose.yml`による開発環境の構築：

```yaml
services:
  comfyui:
    build:
      args:
        MODEL_TYPE: flux1-schnell-gguf  # ビルド時のモデル選択
    environment:
      - NVIDIA_VISIBLE_DEVICES=all      # すべてのGPUを利用可能に
      - SERVE_API_LOCALLY=true          # ローカルAPIサーバーの有効化
    runtime: nvidia                     # NVIDIA GPUランタイムの使用
    ports:
      - "3001:3001"  # Faceswap API
      - "8000:8000"  # RunPod API
      - "8188:8188"  # ComfyUI WebUI
    volumes:
      - ./data/comfyui/output:/comfyui/output  # 生成画像の出力
      - ./data/runpod-volume:/runpod-volume    # 外部モデルストレージ
```

#### GPU設定の詳細

Docker ComposeでGPUを使用するための重要な設定：

1. **runtime: nvidia**
   - Docker内でNVIDIA GPUを使用するための必須設定
   - nvidia-docker2パッケージがホストにインストールされている必要がある

2. **NVIDIA_VISIBLE_DEVICES=all**
   - コンテナから見えるGPUデバイスを指定
   - `all`: すべてのGPU
   - `0,1`: 特定のGPU番号を指定
   - `none`: GPUを使用しない

3. **前提条件**
   - ホストマシンにNVIDIAドライバーがインストール済み
   - nvidia-docker2またはnvidia-container-toolkitがインストール済み
   - Docker Daemonの設定でdefault-runtimeまたはruntimesにnvidiaが設定済み

```bash
# GPU利用可能性の確認
docker run --rm --runtime=nvidia nvidia/cuda:11.8.0-base nvidia-smi
```

## 3. RunPod Handler実装詳細

### 3.1 Handler処理フロー (`src/rp_handler.py`)

```python
def handler(job):
    1. 入力検証 (validate_input)
       - user_photo: ユーザーの顔写真（base64）
       - prompt: 生成プロンプト
       - num_steps: サンプリングステップ数
       - batch_size: バッチサイズ
       - width/height: 画像サイズ

    2. ワークフローテンプレートの読み込み
       - workflow_flux1_schnell_gguf.jsonをロード
       - パラメータの動的更新

    3. ComfyUI APIとの通信
       - check_server(): APIの可用性確認
       - queue_workflow(): ワークフローのキュー追加
       - get_history(): 生成結果のポーリング

    4. 画像生成と後処理
       - process_output_images(): 生成画像の取得
       - swap_face(): 顔交換処理（Faceswap API経由）
       - 肌色チェックによる品質検証

    5. リトライメカニズム
       - 最大3回の再試行
       - 肌色異常時の自動リジェクト
```

### 3.2 RunPodサーバーレス統合

```python
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
```

RunPodは以下の方法でハンドラーを実行：
- **プロダクション環境**: RunPodプラットフォーム上でサーバーレス実行
- **ローカル環境**: `--rp_serve_api`フラグによるAPIサーバー起動

## 4. ComfyUIワークフロー処理

### 4.1 JSONワークフロー構造

```json
{
  "input": {
    "workflow": {
      "node_id": {
        "inputs": {
          // ノード固有の入力パラメータ
        },
        "class_type": "NodeClassName",
        "_meta": {
          "title": "Node Display Name"
        }
      }
    }
  }
}
```

### 4.2 主要ノードタイプと役割

- **DualCLIPLoader**: テキストエンコーダーのロード（T5-XXL + CLIP-L）
- **UnetLoaderGGUF**: GGUF形式の量子化モデルのロード
- **CLIPTextEncode**: プロンプトのエンコーディング
- **EmptyLatentImage**: 初期潜在空間の生成
- **BasicScheduler**: サンプリングスケジュールの設定
- **SamplerCustomAdvanced**: 画像生成サンプリング
- **VAEDecode**: 潜在空間から画像への変換
- **SaveImage**: 生成画像の保存

### 4.3 ワークフローの動的更新

```python
# rp_handler.py内での動的パラメータ更新
for node in workflow.values():
    if node.get("class_type") == "BasicScheduler":
        node["inputs"]["steps"] = num_steps
    elif node.get("class_type") == "EmptyLatentImage":
        node["inputs"]["batch_size"] = batch_size
        node["inputs"]["width"] = width
        node["inputs"]["height"] = height
    elif node.get("class_type") == "CLIPTextEncode":
        node["inputs"]["text"] = prompt
```

## 5. ローカルテスト用APIサーバー

### 5.1 起動スクリプト (`src/start.sh`)

```bash
#!/usr/bin/env bash

# Faceswap APIサーバー（port 3001）
uvicorn server:app --host=0.0.0.0 --port=3001 &

if [ "$SERVE_API_LOCALLY" == "true" ]; then
    # ComfyUI WebUI（port 8188）
    python3 /comfyui/main.py --disable-auto-launch --listen &
    
    # RunPod APIサーバー（port 8000）
    python3 -u /rp_handler.py --rp_serve_api --rp_api_host=0.0.0.0
else
    # プロダクション環境（RunPodプラットフォーム上）
    python3 /comfyui/main.py --disable-auto-launch &
    python3 -u /rp_handler.py
fi
```

### 5.2 APIエンドポイント構成

1. **RunPod API (port 8000)**
   - `/run`: ジョブの実行
   - `/status/{job_id}`: ジョブステータスの確認
   - RunPodのserverless.start()が自動的にAPIサーバーを起動

2. **ComfyUI API (port 8188)**
   - `/prompt`: ワークフローの実行
   - `/history/{prompt_id}`: 実行履歴の取得
   - `/upload/image`: 画像のアップロード

3. **Faceswap API (port 3001)**
   - `/api/runpod`: 顔交換処理のエンドポイント
   - FastAPIによる独立したサービス

## 6. モデル管理とストレージ

### 6.1 モデルファイルの配置

```
/comfyui/models/
├── checkpoints/   # フルモデル（SD, SDXL等）
├── unet/          # UNetモデル（Flux等）
├── clip/          # テキストエンコーダー
├── vae/           # VAEモデル
└── loras/         # LoRAアダプター
```

### 6.2 外部ボリュームサポート

`src/extra_model_paths.yaml`による外部ストレージマウント：
```yaml
runpod-volume:
  base_path: /runpod-volume
  checkpoints: models/checkpoints
  unet: models/unet
  clip: models/clip
  vae: models/vae
```

## 7. エラーハンドリングと監視

### 7.1 リトライメカニズム

- **API可用性チェック**: 最大500回、50ms間隔
- **ワークフロー完了待機**: 最大500回、250ms間隔
- **顔交換処理**: 最大3回の再試行

### 7.2 品質チェック

```python
def is_skin_color_normal(image):
    # HSV色空間での肌色検出
    # 異常な色調の画像を自動的にリジェクト
```

### 7.3 ワーカーリフレッシュ

```python
REFRESH_WORKER = os.environ.get("REFRESH_WORKER", "false")
# ジョブ完了後のワーカー状態リセット
```

## 8. セキュリティと認証

### 8.1 APIトークン管理

- `HUGGINGFACE_ACCESS_TOKEN`: HuggingFaceモデルアクセス
- `CIVITAI_API_KEY`: CivitAIモデルアクセス
- RunPod APIキー: プラットフォーム認証

### 8.2 ローカル環境での隔離

- コンテナ内でのプロセス分離
- ポート制限によるアクセス制御

## 9. デプロイメントプロセス

### 9.1 ローカル開発

```bash
# 環境変数の設定
export HUGGINGFACE_ACCESS_TOKEN=your_token

# コンテナのビルドと起動
docker-compose up --build

# APIテスト
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d @test_input.json
```

### 9.2 RunPodへのデプロイ

1. Dockerイメージのビルド
2. Docker Hubへのプッシュ
3. RunPodテンプレートの作成
4. サーバーレスエンドポイントの設定

## 10. パフォーマンス最適化

### 10.1 メモリ管理

```bash
# TCMallocによるメモリ最適化
export LD_PRELOAD="${TCMALLOC}"
```

### 10.2 モデル最適化

- GGUF量子化による軽量化（Q4_K_S）
- FP8精度によるテキストエンコーダー最適化
- バッチ処理による効率化

## まとめ

このアーキテクチャは、ComfyUIの柔軟なワークフローシステムとRunPodのスケーラブルなインフラストラクチャを統合し、効率的な画像生成サービスを実現しています。Dockerによる環境の統一、マルチステージビルドによる最適化、そして包括的なエラーハンドリングにより、プロダクション環境での安定した運用が可能です。