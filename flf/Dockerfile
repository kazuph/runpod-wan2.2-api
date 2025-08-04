FROM ubuntu:22.04

WORKDIR /content

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=True
ENV PYTHONDONTWRITEBYTECODE=True
ENV PATH="/home/camenduru/.local/bin:/usr/local/cuda/bin:${PATH}"

RUN apt update -y && apt install -y software-properties-common build-essential \
    libgl1 libglib2.0-0 zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev && \
    add-apt-repository -y ppa:git-core/ppa && apt update -y && \
    apt install -y python-is-python3 python3-pip sudo nano aria2 curl wget git git-lfs unzip unrar ffmpeg && \
    aria2c --console-log-level=error -c -x 16 -s 16 -k 1M https://developer.download.nvidia.com/compute/cuda/12.9.1/local_installers/cuda_12.9.1_575.57.08_linux.run -d /content -o cuda_12.9.1_575.57.08_linux.run && sh cuda_12.9.1_575.57.08_linux.run --silent --toolkit && \
    echo "/usr/local/cuda/lib64" >> /etc/ld.so.conf && ldconfig && \
    git clone https://github.com/aristocratos/btop /content/btop && cd /content/btop && make && make install && \
    adduser --disabled-password --gecos '' camenduru && \
    adduser camenduru sudo && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers && \
    chown -R camenduru:camenduru /content && \
    chmod -R 777 /content && \
    chown -R camenduru:camenduru /home && \
    chmod -R 777 /home
    
USER camenduru

RUN pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu128 && \
    pip install xformers --extra-index-url https://download.pytorch.org/whl/cu128 && \
    git clone --depth 1 --branch master https://github.com/comfyanonymous/ComfyUI /content/ComfyUI && cd /content/ComfyUI && pip install -r requirements.txt && \
    pip install opencv-python imageio imageio-ffmpeg ffmpeg-python moviepy timm scikit-image matplotlib diffusers accelerate peft runpod && \
    git clone https://github.com/WASasquatch/was-node-suite-comfyui /content/ComfyUI/custom_nodes/was-node-suite-comfyui && cd /content/ComfyUI/custom_nodes/was-node-suite-comfyui && pip install -r requirements.txt && \
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite /content/ComfyUI/custom_nodes/ComfyUI-VideoHelperSuite && cd /content/ComfyUI/custom_nodes/ComfyUI-VideoHelperSuite && pip install -r requirements.txt && \
    git clone https://github.com/Fannovel16/ComfyUI-WAN /content/ComfyUI/custom_nodes/ComfyUI-WAN

# Download FLF-specific models (separated HIGH/LOW models)
RUN aria2c --console-log-level=error -c -x 16 -s 16 -k 1M https://huggingface.co/Phr00t/WAN2.2-14B-Rapid-AllInOne/resolve/main/Wan2_2-I2V-A14B-HIGH_fp8_e4m3fn_scaled_KJ.safetensors -d /content/ComfyUI/models/unet -o Wan2_2-I2V-A14B-HIGH_fp8_e4m3fn_scaled_KJ.safetensors && \
    aria2c --console-log-level=error -c -x 16 -s 16 -k 1M https://huggingface.co/Phr00t/WAN2.2-14B-Rapid-AllInOne/resolve/main/Wan2_2-I2V-A14B-LOW_fp8_e4m3fn_scaled_KJ.safetensors -d /content/ComfyUI/models/unet -o Wan2_2-I2V-A14B-LOW_fp8_e4m3fn_scaled_KJ.safetensors && \
    aria2c --console-log-level=error -c -x 16 -s 16 -k 1M https://huggingface.co/Phr00t/WAN2.2-14B-Rapid-AllInOne/resolve/main/umt5_xxl_fp8_e4m3fn_scaled.safetensors -d /content/ComfyUI/models/clip -o umt5_xxl_fp8_e4m3fn_scaled.safetensors && \
    aria2c --console-log-level=error -c -x 16 -s 16 -k 1M https://huggingface.co/Phr00t/WAN2.2-14B-Rapid-AllInOne/resolve/main/Wan2_1_VAE_bf16.safetensors -d /content/ComfyUI/models/vae -o Wan2_1_VAE_bf16.safetensors && \
    aria2c --console-log-level=error -c -x 16 -s 16 -k 1M https://huggingface.co/lllyasviel/misc/resolve/main/clip_vision_vit_h.safetensors -d /content/ComfyUI/models/clip_vision -o clip_vision_vit_h.safetensors

# Copy FLF-specific application files
COPY worker_runpod.py /content/worker_runpod.py
COPY generate_video.py /content/generate_video.py  
COPY schema.json /content/schema.json

# Set default command to FLF worker
CMD ["python", "worker_runpod.py"]