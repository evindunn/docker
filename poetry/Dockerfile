FROM evindunn/python3:latest

ARG POETRY_VERSION='2.4.1'

ENV PIPX_BIN_DIR=/usr/local/bin
ENV PIPX_HOME=/opt/pipx

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt upgrade -y
    
RUN python3 -m pip install -U --no-cache-dir pipx && \
    pipx install "poetry~=$POETRY_VERSION"
