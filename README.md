# Docker Images

This repository contains the docker base images I use in my homelab and other
personal projects.

<!-- docker-images-table:start -->
| Image | Base Image | Context | Workflow | Description |
| --- | --- | --- | --- | --- |
| [`evindunn/chronyd:latest`](https://hub.docker.com/r/evindunn/chronyd) | `debian:bookworm-slim` | [chronyd](chronyd) | [.github/workflows/chronyd.yml](.github/workflows/chronyd.yml) | Chrony time server with persistent drift data |
| [`evindunn/debian:trixie-slim`](https://hub.docker.com/r/evindunn/debian) | `debian:trixie-slim` | [debian-trixie-slim](debian-trixie-slim) | [.github/workflows/debian-trixie-slim.yml](.github/workflows/debian-trixie-slim.yml) | Debian base image with custom ca certs |
| [`evindunn/vault-agent:latest`](https://hub.docker.com/r/evindunn/vault-agent) | `evindunn/debian:trixie-slim` | [vault-agent](vault-agent) | [.github/workflows/vault-agent.yml](.github/workflows/vault-agent.yml) | Vault running in agent mode with config templating |
<!-- docker-images-table:end -->

## Skills

This repository includes local Codex skills under [.codex/skills](.codex/skills) for
maintaining Docker workflows and image documentation.

### [create-image](.codex/skills/create-image/SKILL.md)

Creates a GitHub Actions workflow in [.github/workflows](.github/workflows) from an
image slug and build context, and can scaffold the build context directory or a
starter `Dockerfile` when either is missing.

Invoke it by asking Codex to use `create-image`, or run:

```sh
python3 .codex/skills/create-image/scripts/create_image.py --image-slug '<slug>' --build-context '<context>'
```

Example:

```sh
python3 .codex/skills/create-image/scripts/create_image.py --image-slug 'debian:trixie-slim' --build-context 'debian-trixie-slim'
```

### [workflow-image-readme-sync](.codex/skills/workflow-image-readme-sync/SKILL.md)

Scans [.github/workflows](.github/workflows) for Docker images built by this repo and
updates the managed Docker image table in [README.md](README.md).

Invoke it by asking Codex to use `workflow-image-readme-sync`, or run:

```sh
python3 .codex/skills/workflow-image-readme-sync/scripts/update_readme.py
```
