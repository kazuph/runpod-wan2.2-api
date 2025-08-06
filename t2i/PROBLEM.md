# WAN2.1 T2I 実装の問題点

## 現在の状況

WAN2.1 T2I（Text-to-Image）の実装は、インフラストラクチャは完成していますが、実際のモデル推論が動作していません。

## 主な問題

### ComfyUI-WanVideoWrapperのノード読み込み失敗

**症状：**
- `Loaded 64 WanVideo nodes` と表示されるが、実際には `Available WanVideo nodes: []` となる
- WanVideoノード（LoadWanVideoT5TextEncoder、WanVideoSampler等）が利用できない

**原因：**
1. **相対インポートの問題**
   ```python
   # ComfyUI-WanVideoWrapper/__init__.py
   from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
   ```
   このような相対インポートが、モジュールとして正しくロードされていない時に失敗する

2. **モジュール名の衝突**
   - ComfyUIの標準 `nodes.py` と WanVideoWrapper内の `nodes.py` が衝突
   - `importlib.import_module("nodes")` が誤って標準のnodesをインポートしている可能性

3. **依存関係の問題**
   - WanVideoWrapperが依存する内部モジュール（wanvideo.modules.model等）が正しくパスに含まれていない

## 試みた解決策

1. **直接的なモジュールインポート** ❌
   ```python
   wan_module = importlib.import_module("nodes")
   ```
   → 標準のnodesモジュールをインポートしてしまう

2. **パッケージとしてのインポート** ❌
   ```python
   spec = importlib.util.spec_from_file_location(
       "ComfyUI_WanVideoWrapper",
       os.path.join(wanvideo_path, "__init__.py")
   )
   ```
   → 相対インポートエラー

3. **main.load_custom_nodes()の使用** ❌
   ```python
   main.load_custom_nodes()
   ```
   → serverモジュールの循環参照エラー

4. **JSONワークフローの直接実行** ❌
   - ノードが読み込まれていないため、ワークフロー検証で失敗

## 動作している部分

- ✅ Dockerコンテナの構築と起動
- ✅ APIサーバー（ポート8083）
- ✅ すべてのモデルファイルのダウンロード（約23GB）
- ✅ CLIツール
- ✅ テスト画像生成機能

## 未解決の技術的課題

1. **ComfyUIのカスタムノードローダーの正しい使用方法**
   - カスタムノードが期待する環境設定
   - 適切な初期化順序

2. **Python モジュールシステムの制約**
   - 相対インポートを含むパッケージの動的ロード
   - sys.pathの管理

3. **ComfyUIアーキテクチャの理解**
   - ノード登録メカニズム
   - 実行コンテキストの要件

## 可能な回避策

1. **ComfyUIサーバーを別プロセスで起動**
   - main.pyを直接実行してHTTP API経由で通信

2. **ノードを手動で実装**
   - WanVideoノードの機能を独自に再実装

3. **他の推論フレームワークを使用**
   - ComfyUIを使わず、diffusersなどで直接実装

## 結論

現時点では、ComfyUI-WanVideoWrapperのカスタムノードを正しく読み込むことができず、WAN2.1モデルの実際の推論は実行できません。しかし、必要なインフラストラクチャとモデルファイルはすべて準備されているため、ノード読み込み問題が解決されれば、すぐに動作可能な状態です。