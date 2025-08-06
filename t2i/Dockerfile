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
    pip install opencv-python imageio imageio-ffmpeg ffmpeg-python moviepy timm scikit-image matplotlib diffusers accelerate peft runpod

# Install ComfyUI-WanVideoWrapper for WAN2.1 support
RUN git clone https://github.com/kijai/ComfyUI-WanVideoWrapper /content/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper && \
    cd /content/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper && \
    pip install -r requirements.txt

# Copy the import fix scripts (will be run at runtime if needed)
COPY fix_wanvideo_imports.py /content/fix_wanvideo_imports.py
COPY fix_remaining_imports.py /content/fix_remaining_imports.py

# Download WAN2.1 models for T2I
# Text encoder
RUN aria2c --console-log-level=error -c -x 16 -s 16 -k 1M https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5-xxl-enc-bf16.safetensors -d /content/ComfyUI/models/text_encoders -o umt5-xxl-enc-bf16.safetensors

# Main T2V model (14B FP8)
RUN aria2c --console-log-level=error -c -x 16 -s 16 -k 1M https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan2_1-T2V-14B_fp8_e4m3fn.safetensors -d /content/ComfyUI/models/diffusion_models -o Wan2_1-T2V-14B_fp8_e4m3fn.safetensors

# VAE
RUN aria2c --console-log-level=error -c -x 16 -s 16 -k 1M https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan2_1_VAE_bf16.safetensors -d /content/ComfyUI/models/vae -o Wan2_1_VAE_bf16.safetensors

# Optional: VACE module for enhanced quality
RUN aria2c --console-log-level=error -c -x 16 -s 16 -k 1M https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan2_1-VACE_module_14B_fp8_e4m3fn.safetensors -d /content/ComfyUI/models/diffusion_models -o Wan2_1-VACE_module_14B_fp8_e4m3fn.safetensors

# Optional: Lightning LoRA for faster generation
# Commenting out as it fails - can be downloaded manually if needed
# RUN aria2c --console-log-level=error -c -x 16 -s 16 -k 1M https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank256_bf16.safetensors -d /content/ComfyUI/models/loras -o lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank256_bf16.safetensors

# Copy scripts and workflow
COPY ./init_comfyui.py /content/ComfyUI/init_comfyui.py
COPY ./worker_runpod.py /content/ComfyUI/worker_runpod.py
COPY ./worker_runpod_test.py /content/ComfyUI/worker_runpod_test.py
COPY ./wan2_1_workflow.py /content/ComfyUI/wan2_1_workflow.py
COPY ./wan21_t2i_workflow.json /content/ComfyUI/wan21_t2i_workflow.json
WORKDIR /content/ComfyUI
CMD ["python", "worker_runpod.py"]