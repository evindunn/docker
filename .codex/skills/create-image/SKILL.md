---
name: create-image
description: Create a GitHub Actions Docker build workflow in .github/workflows from an image slug and build context, and scaffold the build context directory or Dockerfile when they do not already exist. Use this when asked to add a new image in this repository.
---

# Create Image

Use this skill when the user wants a new Docker image added to this repository, including its build context and a thin GitHub Actions wrapper workflow under [../../../.github/workflows](../../../.github/workflows).

## Inputs

- Image slug such as `debian:trixie-slim`
- Build context such as `debian-trixie-slim`

## Workflow

1. Run `python3 scripts/create_image.py --image-slug <slug> --build-context <context>`.
2. If the build context directory does not exist, let the generator create it.
3. If the build context does not contain a `Dockerfile`, let the generator scaffold one with `FROM <image-slug>`.
4. Review the generated wrapper workflow under [../../../.github/workflows](../../../.github/workflows) and make sure it passes `image`, `tag`, and `context` into the reusable base workflow.
5. Make sure the `paths` filters include the workflow file, the reusable base workflow, the shared README check script, the build context, and shared assets under [../../../shared](../../../shared).

## Notes

- The generator assumes the Docker Hub namespace is `evindunn`, matching the workflows already in this repo.
- The workflow file name is derived from the build context and written as `<build-context>.yml`.
- When it scaffolds a missing `Dockerfile`, the initial contents are based on the provided image slug.
- The reusable base workflow lives at [../../../.github/workflows/build-image-base.yml](../../../.github/workflows/build-image-base.yml).
- Wrapper workflows pass `image`, `tag`, and `context` into the reusable base workflow and inherit repository secrets.
- The reusable workflow runs `.github/workflows/check_readme_image.py` before `docker build` so undocumented images fail fast.
- The reusable workflow uses `docker/setup-qemu-action`, `docker/setup-buildx-action`, and a shared auxiliary build context at `./shared`.
- The reusable workflow publishes multi-arch images for both `linux/amd64` and `linux/arm64`.
- The generated workflow builds from the provided context path and pushes `evindunn/<image-slug>`.
