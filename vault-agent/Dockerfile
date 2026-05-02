FROM evindunn/debian:trixie-slim

# buildx will automatically set this, which is nice
ARG TARGETARCH

ENV GOMPLATE_VERSION=3.11.5

COPY vault-ca.crt /usr/local/share/ca-certificates/

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    update-ca-certificates && \
    apt-get -qq update && \
    apt-get -qq install --no-install-recommends -y \
        wget \
        gnupg2 \
        lsb-release \
    && \
    wget -qO- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" > /etc/apt/sources.list.d/hashicorp.list && \
    apt-get -qq update && \
    apt-get -qq install vault && \
    useradd -m -s /bin/bash vault-agent && \
    mkdir /data /secrets && \
    chown vault-agent:vault-agent /data /secrets
    
RUN wget -qO /usr/local/bin/gomplate https://github.com/hairyhenderson/gomplate/releases/download/v${GOMPLATE_VERSION}/gomplate_linux-${TARGETARCH} && \
    chmod +x /usr/local/bin/gomplate

# Copy data for add-on
COPY --chmod=755 docker-entrypoint.sh /
COPY --chmod=444 vault-agent.ctmpl /
COPY --chmod=444 tls-pair.tmpl /
VOLUME /secrets

USER vault-agent
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["vault", "agent", "-config=/data/vault-agent.hcl", "-log-level=info"]
