FROM evindunn/python3:latest

ARG POETRY_VERSION='2.4.1'
ENV POETRY_VIRTUALENVS_PATH=/opt/poetry/venvs
ENV POETRY_CACHE_DIR=/opt/poetry/cache

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt upgrade -y
    
RUN pipx install "poetry~=$POETRY_VERSION"
