# Docker Images

This repository contains the docker base images I use in my homelab and other
personal projects.

<!-- docker-images-table:start -->
| Image | Base Image | Context | Workflow | Description |
| --- | --- | --- | --- | --- |
| [`evindunn/debian:trixie-slim`](https://hub.docker.com/r/evindunn/debian) | `debian:trixie-slim` | [debian-trixie-slim](debian-trixie-slim) | [.github/workflows/debian-trixie-slim.yml](.github/workflows/debian-trixie-slim.yml) | Docker image that adds `ca-certificates`, and installs local CA certificate from `localdomain.net.crt`. |
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
python3 .codex/skills/create-image/scripts/create_workflow.py --image-slug '<slug>' --build-context '<context>'
```

Example:

```sh
python3 .codex/skills/create-image/scripts/create_workflow.py --image-slug 'debian:trixie-slim' --build-context 'debian-trixie-slim'
```

### [workflow-image-readme-sync](.codex/skills/workflow-image-readme-sync/SKILL.md)

Scans [.github/workflows](.github/workflows) for Docker images built by this repo and
updates the managed Docker image table in [README.md](README.md).

Invoke it by asking Codex to use `workflow-image-readme-sync`, or run:

```sh
python3 .codex/skills/workflow-image-readme-sync/scripts/update_readme.py
```
