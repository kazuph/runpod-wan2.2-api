# HuggingFace認証設定ガイド

## 1. HuggingFaceアクセストークンの作成

1. [HuggingFace Settings](https://huggingface.co/settings/tokens)にアクセス
2. "New token"をクリック
3. トークン名を入力（例：wan22-download）
4. "Type"は"Read"を選択（モデルダウンロードのみなら読み取り権限で十分）
5. "Generate token"をクリック

## 2. 認証方法

### 方法A: HuggingFace CLIを使用（推奨）

```bash
# HuggingFace CLIをインストール
pip install "huggingface_hub[cli]"

# ログイン（トークンを求められるので入力）
huggingface-cli login

# または環境変数を使用
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
huggingface-cli login --token $HF_TOKEN
```

### 方法B: Dockerコンテナ内で認証

```bash
# コンテナ内でログイン
docker exec -it comfyui-wan22-test bash
huggingface-cli login
```

### 方法C: docker-compose.ymlに環境変数として設定

```yaml
environment:
  - HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 3. WAN2.2モデルのダウンロード

認証後、以下のコマンドでモデルをダウンロード：

```bash
# 5Bモデル
huggingface-cli download Wan-AI/Wan2.2-TI2V-5B --local-dir ./models/wan2.2-5B

# 14Bモデル（T2V）
huggingface-cli download Wan-AI/Wan2.2-T2V-A14B --local-dir ./models/wan2.2-t2v-14B

# 14Bモデル（I2V）
huggingface-cli download Wan-AI/Wan2.2-I2V-A14B --local-dir ./models/wan2.2-i2v-14B
```

## 4. 個別ファイルのダウンロード（ComfyUI用）

```bash
# VAEファイル
huggingface-cli download Wan-AI/Wan2.2-TI2V-5B wan2.2_vae.safetensors --local-dir ./models/vae

# テキストエンコーダー
huggingface-cli download Wan-AI/Wan2.2-TI2V-5B umt5_xxl_fp8_e4m3fn_scaled.safetensors --local-dir ./models/text_encoders

# Diffusionモデル
huggingface-cli download Wan-AI/Wan2.2-TI2V-5B wan2.2_ti2v_5B_fp16.safetensors --local-dir ./models/diffusion_models
```

## トラブルシューティング

### 401エラーが続く場合

1. トークンの権限を確認（Readアクセスがあるか）
2. `huggingface-cli logout`してから再度ログイン
3. `huggingface-cli auth whoami`で認証状態を確認
4. ブラウザでモデルページにアクセスできるか確認

### 注意事項

- WAN2.2モデルは**ゲート付きモデルではない**ため、特別な承認は不要
- Apache 2.0ライセンスで公開されている
- ダウンロードには安定したインターネット接続が必要（数GB規模）