# ComfyUI WAN2.2 GGUF Image-to-Video Generation Dockerfile
# Reverse engineered from nykk3/comfyui-wan2.2-gguf:q4ks-14b-i2v-cuda12.8

# Use NVIDIA CUDA base image with CUDA 12.8
FROM nvidia/cuda:12.6.2-cudnn-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=$CUDA_HOME/bin:$PATH
ENV LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    git \
    wget \
    curl \
    unzip \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgoogle-perftools4 \
    libtcmalloc-minimal4 \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Clone ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /app/ComfyUI

# Install Python dependencies for ComfyUI
WORKDIR /app/ComfyUI
RUN pip3 install --no-cache-dir \
    torch==2.4.0 \
    torchvision==0.19.0 \
    torchaudio==2.4.0 \
    --index-url https://download.pytorch.org/whl/cu121

RUN pip3 install --no-cache-dir \
    -r requirements.txt \
    xformers \
    accelerate \
    transformers \
    diffusers \
    opencv-python \
    pillow \
    numpy \
    scipy \
    scikit-image \
    matplotlib \
    imageio \
    imageio-ffmpeg \
    psutil \
    kornia \
    spandrel \
    soundfile \
    GitPython

# Install ComfyUI Manager
RUN cd custom_nodes && \
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git

# Install WAN2.2 related custom nodes
RUN cd custom_nodes && \
    git clone https://github.com/kijai/ComfyUI-KwaiKolorsWrapper.git && \
    git clone https://github.com/kijai/ComfyUI-VideoCrafter.git && \
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git && \
    git clone https://github.com/Fannovel16/comfyui_controlnet_aux.git

# Install additional dependencies for video processing
RUN pip3 install --no-cache-dir \
    moviepy \
    av \
    decord \
    einops \
    omegaconf \
    safetensors \
    huggingface-hub \
    timm \
    controlnet-aux

# Create models directory structure
RUN mkdir -p /app/ComfyUI/models/checkpoints && \
    mkdir -p /app/ComfyUI/models/vae && \
    mkdir -p /app/ComfyUI/models/clip && \
    mkdir -p /app/ComfyUI/models/controlnet && \
    mkdir -p /app/ComfyUI/models/diffusers && \
    mkdir -p /app/ComfyUI/models/unet && \
    mkdir -p /app/ComfyUI/models/wan2.2

# Download WAN2.2 GGUF models (Q4KS quantization)
# Note: These are large downloads (~17GB+ total)
WORKDIR /app/ComfyUI/models/wan2.2

# Download WAN2.2-14B GGUF model (Q4KS quantization)
RUN wget -O wan2.2-14b-i2v-q4ks.gguf \
    "https://huggingface.co/kwaikeg/WAN2.2-14B-I2V/resolve/main/wan2.2-14b-i2v-q4ks.gguf" || \
    echo "Model download failed - please download manually"

# Download associated model files
RUN wget -O text_encoder.safetensors \
    "https://huggingface.co/kwaikeg/WAN2.2-14B-I2V/resolve/main/text_encoder.safetensors" || \
    echo "Text encoder download failed - please download manually"

RUN wget -O scheduler_config.json \
    "https://huggingface.co/kwaikeg/WAN2.2-14B-I2V/resolve/main/scheduler_config.json" || \
    echo "Scheduler config download failed - please download manually"

RUN wget -O model_index.json \
    "https://huggingface.co/kwaikeg/WAN2.2-14B-I2V/resolve/main/model_index.json" || \
    echo "Model index download failed - please download manually"

# Install GGUF support for ComfyUI (if needed)
WORKDIR /app/ComfyUI/custom_nodes
RUN git clone https://github.com/city96/ComfyUI-GGUF.git || echo "GGUF node already exists"

# Install additional Python packages for GGUF support
RUN pip3 install --no-cache-dir \
    gguf \
    llama-cpp-python

# Set up environment for CUDA memory optimization
ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
ENV CUDA_LAUNCH_BLOCKING=0

# Create startup script
WORKDIR /app
RUN echo '#!/bin/bash\ncd /app/ComfyUI\npython3 main.py --listen 0.0.0.0 --port 8188 --cuda-device 0' > start.sh && \
    chmod +x start.sh

# Expose ComfyUI port
EXPOSE 8188

# Set working directory back to ComfyUI
WORKDIR /app/ComfyUI

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8188/ || exit 1

# Default command
CMD ["python3", "main.py", "--listen", "0.0.0.0", "--port", "8188", "--cuda-device", "0"]