FROM debian:trixie-slim

RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lib,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt upgrade -y && \
    apt install -y \
	ca-certificates

COPY --from=shared localdomain.net.crt /usr/local/share/ca-certificates/

RUN update-ca-certificates
