---
name: workflow-image-readme-sync
description: Scan .github/workflows for Docker images built and pushed by this repository, then update the README.md image table with the discovered images, base images, build contexts, workflow paths, and concise agent-written descriptions based on each build context. Use this when asked to sync repository Docker image documentation from GitHub Actions workflows.
---

# Workflow Image README Sync

Use this skill when the user wants `README.md` updated from Docker image definitions in [`.github/workflows`](../../../.github/workflows).

## Workflow

1. Run `python3 .codex/skills/workflow-image-readme-sync/scripts/update_readme.py --print-discovery-json` to discover images, base images, build contexts, and workflow paths.
2. Read each discovered build context, starting with its `Dockerfile` and only the nearby files needed to understand the image's purpose.
3. Write concise human descriptions in the style of product summaries, not low-level Dockerfile narration.
4. Save the descriptions in a JSON mapping from image name to description, then run `python3 .codex/skills/workflow-image-readme-sync/scripts/update_readme.py --description-file <file>`.
5. Check the updated table in [`README.md`](../../../README.md) and verify each row includes `Image`, `Base Image`, `Context`, a `Workflow` badge that links to the GitHub Actions workflow, and `Description`.

## Notes

- The updater rewrites only the content between the `<!-- docker-images-table:start -->` and `<!-- docker-images-table:end -->` markers in [`README.md`](../../../README.md).
- The Python script is intentionally data-oriented. It discovers image metadata and renders the table, but the agent is responsible for the final description quality.
- The `Workflow` column should render GitHub Actions badge images that link to each workflow page, rather than plain text workflow paths.
- Prefer short summaries like `Debian base image with custom ca certs` or `Vault running in agent mode with config templating`.
- If no images are found, the table is populated with a single `None` row so the README stays explicit.
