# HF Spaces runs containers as non-root on port 7860 by default.
#
# Base image: nvidia/cuda so llama-cpp-python builds with CUDA support when the
# `model` group installs. On a GPU Space (T4, A10G, etc.) llama.cpp will
# auto-offload all layers. On a CPU Space the CUDA libs go unused — same image,
# either hardware target.
#
# On first boot the GGUF is pulled from the HF Hub into
# /home/user/.cache/huggingface, which Spaces persists across restarts.
#
# Expect a long first boot: image build (~5-10 min — llama-cpp-python compiles
# from source against CUDA), GGUF download (~1 min), model load into VRAM (~15s).

FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-venv \
        python3-pip \
        ffmpeg \
        build-essential \
        cmake \
        git \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/local/bin/python3 \
    && ln -sf /usr/bin/python3.11 /usr/local/bin/python

# HF Spaces requires a non-root user with UID 1000.
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"
WORKDIR /home/user/app

RUN pip install --no-cache-dir --user uv

# Tell llama-cpp-python's build to enable CUDA.
ENV CMAKE_ARGS="-DGGML_CUDA=on"
ENV FORCE_CMAKE=1

COPY --chown=user:user pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --group model

COPY --chown=user:user . .

# config.py defaults LLAMA_N_GPU_LAYERS=-1 → offload all layers when CUDA is
# visible, otherwise llama.cpp falls back to CPU automatically.
ENV HF_HOME=/home/user/.cache/huggingface
ENV PORT=7860
EXPOSE 7860

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
