# HF Spaces runs containers as non-root on port 7860 by default.
#
# We install llama-cpp-python from the project's prebuilt CUDA 12.4 wheel index
# instead of compiling from source. Compiling against CUDA peaks >10GB RSS and
# reliably OOMs HF's shared builder on anything below a paid GPU tier.
#
# On first boot the GGUF is pulled from the HF Hub into
# /home/user/.cache/huggingface (persisted across restarts).

FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-venv \
        python3-pip \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/local/bin/python3 \
    && ln -sf /usr/bin/python3.11 /usr/local/bin/python

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"
WORKDIR /home/user/app

RUN pip install --no-cache-dir --user uv

# Pull everything except llama-cpp-python via uv (fast, cached).
# We strip it from the model group by copying only the files uv needs.
COPY --chown=user:user pyproject.toml uv.lock ./

# Base deps (eval metrics now ship as part of runtime dependencies). The `model`
# group is installed manually below with prebuilt CUDA wheels to avoid the 10GB+
# source compile of llama-cpp-python.
RUN uv sync --frozen --no-dev

# Now install model deps manually, using the prebuilt CUDA wheel for llama-cpp.
# --system installs into the uv-managed venv since we're running inside it.
RUN uv pip install \
        --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124 \
        llama-cpp-python \
        openai-whisper \
        huggingface-hub

COPY --chown=user:user . .

# config.py defaults LLAMA_N_GPU_LAYERS=-1 → offload everything to CUDA.
ENV HF_HOME=/home/user/.cache/huggingface
ENV PORT=7860
EXPOSE 7860

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
