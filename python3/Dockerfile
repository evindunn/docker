FROM evindunn/debian:trixie-slim

ENV PIPX_BIN_DIR=/usr/local/bin
ENV PIPX_HOME=/opt/pipx

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt upgrade -y && \
    apt install -y python3-pip python3-venv pipx
    
RUN pipx ensurepath --global --prepend
RUN printf '[global]\nno-cache-dir = false' > /etc/pip.conf
