FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

WORKDIR /

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 python3-pip git wget curl ffmpeg \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set Python aliases
RUN ln -s /usr/bin/python3 /usr/bin/python

# Install PyTorch 2.3+ with float8 support
RUN pip install --no-cache-dir \
    torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu118 && \
    pip install --no-cache-dir xformers==0.0.27

# Clone and install ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /comfyui && \
    cd /comfyui && \
    pip install --no-cache-dir -r requirements.txt

# Install additional Python packages
RUN pip install --no-cache-dir \
    runpod \
    opencv-python \
    imageio imageio-ffmpeg \
    ffmpeg-python \
    moviepy \
    Pillow \
    numpy \
    requests

# Install ComfyUI custom nodes
RUN cd /comfyui/custom_nodes && \
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite && \
    cd ComfyUI-VideoHelperSuite && \
    pip install --no-cache-dir -r requirements.txt && \
    cd /comfyui/custom_nodes && \
    git clone https://github.com/city96/ComfyUI-GGUF && \
    cd ComfyUI-GGUF && \
    pip install --no-cache-dir -r requirements.txt

# Create model directories
RUN mkdir -p /comfyui/models/unet \
    /comfyui/models/clip \
    /comfyui/models/vae \
    /comfyui/models/checkpoints \
    /comfyui/input \
    /comfyui/output

# Models will be mounted from host or downloaded at runtime
RUN echo "Models will be mounted from host volume"

# Copy application files
COPY worker_flf_proper.py /worker_flf_proper.py
COPY rp_handler.py /rp_handler.py
COPY start.sh /start.sh
COPY Wan2.2_14B_flf_720.json /workflow.json

# Make scripts executable
RUN chmod +x /start.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SERVE_API_LOCALLY=false

# Expose ports
EXPOSE 8080 8188

# Set entrypoint for proper video output
ENTRYPOINT ["python", "/worker_flf_proper.py"]