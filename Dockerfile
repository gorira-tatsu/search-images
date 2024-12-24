FROM nvidia/cuda:12.6.2-cudnn-runtime-ubuntu22.04

ENV PIP_NO_CACHE_DIR=off \
    PIP_DEFAULT_TIMEOUT=100 \
    CUDA_HOME=/usr/local/cuda \
    PATH="/root/.local/bin/:/opt/venv/bin:$PATH"
    
# LD_LIBRARY_PATH="/usr/local/cuda"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

FROM python:3.9.20-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY ./pyproject.toml /app/

RUN uv sync

# CMD ["back-venv/bin/fastapi", "run", "main.py", "--port", "8100", "--host", "0.0.0.0"]
CMD ["bash", "run.sh"]

#docker run -v ./:/app my_image
#:/app# export LD_LIBRARY_PATH=/usr/local/cuda
#:/app# pip uninstall torch