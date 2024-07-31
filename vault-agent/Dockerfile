FROM debian:bookworm-slim

RUN apt-get -qq update && \
    apt-get -qq install -y \
        wget \
        gnupg2 \
        lsb-release \
    && \
    wget -qO- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" > /etc/apt/sources.list.d/hashicorp.list && \
    apt-get -qq update && \
    apt-get -qq install vault && \
    apt clean all && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash vault-agent && \
    mkdir /data /secrets && \
    chown vault-agent:vault-agent /data /secrets

# Copy data for add-on
COPY --from=hairyhenderson/gomplate:stable /gomplate /bin/gomplate
COPY --chmod=755 docker-entrypoint.sh /
COPY --chmod=644 vault-agent.tmpl /
VOLUME /secrets

USER vault-agent
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["vault", "agent", "-config=/data/config.hcl", "-log-level=info"]
