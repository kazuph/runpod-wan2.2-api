#!/bin/bash
# Test script for ComfyUI WAN2.2 GGUF container

set -e

echo "🐳 Testing ComfyUI WAN2.2 GGUF Container"
echo "======================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running or not accessible"
    exit 1
fi

# Check for NVIDIA Docker support
if ! docker run --rm --gpus all nvidia/cuda:12.8-base nvidia-smi >/dev/null 2>&1; then
    echo "❌ NVIDIA Docker support not available"
    echo "Please install nvidia-container-toolkit"
    exit 1
fi

echo "✅ Docker and NVIDIA support confirmed"

# Build the container
echo ""
echo "🔨 Building ComfyUI WAN2.2 GGUF container..."
echo "Note: This will take 1-2 hours due to large model downloads"

read -p "Build with model downloads? (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    DOWNLOAD_MODELS=true
    echo "Building with model downloads..."
    docker build -f Dockerfile.optimized \
        --build-arg DOWNLOAD_MODELS=true \
        -t comfyui-wan22-gguf:test .
else
    DOWNLOAD_MODELS=false
    echo "Building without model downloads..."
    docker build -f Dockerfile.optimized \
        --build-arg DOWNLOAD_MODELS=false \
        -t comfyui-wan22-gguf:test .
fi

echo "✅ Container built successfully"

# Create test directories
mkdir -p ./test-output ./test-input
echo "📁 Created test directories"

# Run the container
echo ""
echo "🚀 Starting container for testing..."
docker run -d \
    --name comfyui-wan22-test \
    --gpus all \
    -p 8188:8188 \
    -v $(pwd)/test-output:/app/ComfyUI/output \
    -v $(pwd)/test-input:/app/ComfyUI/input \
    comfyui-wan22-gguf:test

echo "⏳ Waiting for ComfyUI to start (this may take 60-120 seconds)..."
sleep 30

# Wait for health check
MAX_RETRIES=12
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -s -f http://localhost:8188/ >/dev/null 2>&1; then
        echo "✅ ComfyUI is responding!"
        break
    fi
    RETRY=$((RETRY+1))
    echo "⏳ Attempt $RETRY/$MAX_RETRIES - waiting 10s..."
    sleep 10
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    echo "❌ ComfyUI failed to start within timeout"
    docker logs comfyui-wan22-test
    exit 1
fi

# Test API endpoint
echo ""
echo "🔍 Testing API endpoints..."

# Test system info
if curl -s http://localhost:8188/system_stats | grep -q "system"; then
    echo "✅ System stats API working"
else
    echo "⚠️  System stats API not responding as expected"
fi

# Test queue status
if curl -s http://localhost:8188/queue | grep -q "queue_running\|queue_pending"; then
    echo "✅ Queue API working"
else
    echo "⚠️  Queue API not responding as expected"
fi

# Show container info
echo ""
echo "📊 Container Information:"
echo "------------------------"
docker exec comfyui-wan22-test nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "GPU info not available"

if [ "$DOWNLOAD_MODELS" = true ]; then
    echo ""
    echo "🎯 Model Information:"
    echo "--------------------"
    docker exec comfyui-wan22-test ls -lh /app/ComfyUI/models/wan2.2/ 2>/dev/null || echo "Models directory not accessible"
fi

echo ""
echo "🌐 Access URLs:"
echo "  WebUI: http://localhost:8188"
echo "  API:   http://localhost:8188/docs"

echo ""
echo "🎉 Container test completed successfully!"
echo ""
echo "To stop and clean up:"
echo "  docker stop comfyui-wan22-test"
echo "  docker rm comfyui-wan22-test"
echo "  docker rmi comfyui-wan22-gguf:test"

# Keep container running for manual testing
echo ""
echo "Container is running. Press Ctrl+C to stop and cleanup..."
trap 'echo ""; echo "🛑 Cleaning up..."; docker stop comfyui-wan22-test >/dev/null 2>&1; docker rm comfyui-wan22-test >/dev/null 2>&1; echo "✅ Cleanup complete"; exit 0' INT

# Show logs in real-time
docker logs -f comfyui-wan22-test