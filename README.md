# Docker Images

This repository contains the docker base images I use in my homelab and other
personal projects.

<!-- docker-images-table:start -->
| Image | Base Image | Context | Workflow | Description |
| --- | --- | --- | --- | --- |
| [`evindunn/chronyd:latest`](https://hub.docker.com/r/evindunn/chronyd) | `evindunn/debian:trixie-slim` | [chronyd](chronyd) | [![chronyd.yml build status](https://github.com/evindunn/docker/actions/workflows/chronyd.yml/badge.svg)](https://github.com/evindunn/docker/actions/workflows/chronyd.yml) | Chrony NTP server on Debian Trixie-slim, persisting state and exposing UDP NTP/NTS ports. |
| [`evindunn/debian:trixie-slim`](https://hub.docker.com/r/evindunn/debian) | `debian:trixie-slim` | [debian-trixie-slim](debian-trixie-slim) | [![debian-trixie-slim.yml build status](https://github.com/evindunn/docker/actions/workflows/debian-trixie-slim.yml/badge.svg)](https://github.com/evindunn/docker/actions/workflows/debian-trixie-slim.yml) | Debian Trixie slim base image with custom CA certificates installed. |
| [`evindunn/python3:latest`](https://hub.docker.com/r/evindunn/python3) | `evindunn/debian:trixie-slim` | [python3](python3) | [![python3.yml build status](https://github.com/evindunn/docker/actions/workflows/python3.yml/badge.svg)](https://github.com/evindunn/docker/actions/workflows/python3.yml) | Debian Trixie slim image with Python 3 (pip, venv) for lightweight Python runtimes. |
| [`evindunn/vault-agent:latest`](https://hub.docker.com/r/evindunn/vault-agent) | `evindunn/debian:trixie-slim` | [vault-agent](vault-agent) | [![vault-agent.yml build status](https://github.com/evindunn/docker/actions/workflows/vault-agent.yml/badge.svg)](https://github.com/evindunn/docker/actions/workflows/vault-agent.yml) | Vault agent image with gomplate, AppRole auth, and Vault PKI TLS cert templating. |
<!-- docker-images-table:end -->

## Skills

This repository includes local Codex skills under [.codex/skills](.codex/skills) for
maintaining Docker workflows and image documentation.

### [create-image](.codex/skills/create-image/SKILL.md)

Creates a GitHub Actions workflow in [.github/workflows](.github/workflows) from an
image slug and build context, and can scaffold the build context directory or a
starter `Dockerfile` when either is missing.

Invoke it with `$create-image`, or run:

```sh
python3 scripts/create_image.py --image-slug '<slug>' --build-context '<context>'
```

Example:

```sh
python3 scripts/create_image.py --image-slug 'debian:trixie-slim' --build-context 'debian-trixie-slim'
```

### [workflow-image-readme-sync](.codex/skills/workflow-image-readme-sync/SKILL.md)

Scans [.github/workflows](.github/workflows) for Docker images built by this repo and
updates the managed Docker image table in [README.md](README.md).

Invoke it with `$workflow-image-readme-sync`, or run:

```sh
python3 scripts/update_readme.py
```
