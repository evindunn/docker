FROM evindunn/debian:trixie-slim

ENV PIPX_BIN_DIR=/usr/local/bin
ENV PIPX_HOME=/opt/pipx

# Disable pip cache by default
ENV PIP_NO_CACHE_DIR=false

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt upgrade -y && \
    apt install -y \
        git \
        pipx \
        python3-pip \
        python3-venv

RUN pipx ensurepath --global --prepend && \
    ln -sf $(which python3) /usr/local/bin/python
