---
name: workflow-image-readme-sync
description: Scan .github/workflows for Docker images built and pushed by this repository, then update the README.md image table with the discovered images, base images, build contexts, workflow paths, and inferred descriptions from each build context. Use this when asked to sync repository Docker image documentation from GitHub Actions workflows.
---

# Workflow Image README Sync

Use this skill when the user wants `README.md` updated from Docker image definitions in [`.github/workflows`](../../../.github/workflows).

## Workflow

1. Review the workflow files under [`.github/workflows`](../../../.github/workflows) to confirm how images are named and where each build context lives.
2. Run `python3 .codex/skills/workflow-image-readme-sync/scripts/update_readme.py`.
3. Check the updated table in [`README.md`](../../../README.md) and verify each row includes `Image`, `Base Image`, `Context`, `Workflow`, and `Description`.

## Notes

- The updater rewrites only the content between the `<!-- docker-images-table:start -->` and `<!-- docker-images-table:end -->` markers in [`README.md`](../../../README.md).
- The updater tries to infer the description from the build context, primarily by reading the context `Dockerfile` and looking for installed packages, copied certificates, and similar setup hints.
- If no images are found, the table is populated with a single `None` row so the README stays explicit.
