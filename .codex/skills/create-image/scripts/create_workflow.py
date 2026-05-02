#!/usr/bin/env python3
"""Create a GitHub Actions workflow for building and pushing a Docker image."""

import argparse
import pathlib
import re
import sys


DEFAULT_DOCKERHUB_NAMESPACE = 'evindunn'
WORKFLOW_DIR = pathlib.Path('.github/workflows')


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Create a Docker image build workflow for this repository.',
    )
    parser.add_argument(
        '--image-slug',
        required=True,
        help='Image slug to publish under the default Docker Hub namespace, for example debian:trixie-slim.',
    )
    parser.add_argument(
        '--build-context',
        required=True,
        help='Build context directory relative to the repository root.',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print the workflow content instead of writing it.',
    )
    return parser.parse_args()


def normalize_build_context(build_context: str) -> str:
    """Normalize the provided build context path."""
    normalized = build_context.strip()
    if normalized == '.':
        return normalized

    normalized = normalized.removeprefix('./').strip('/')
    return normalized or '.'


def validate_image_slug(image_slug: str) -> None:
    """
    Validate the Docker image slug format.

    :param image_slug: Image slug without the namespace prefix.
    :raises ValueError: If the slug contains unsupported characters.
    """
    if not re.fullmatch(r'[a-z0-9]+(?:[._-][a-z0-9]+)*(?::[A-Za-z0-9._-]+)?', image_slug):
        raise ValueError(
            'image slug must look like "name" or "name:tag" and use Docker-safe characters',
        )


def resolve_build_context(repo_root: pathlib.Path, build_context: str) -> pathlib.Path:
    """
    Resolve the build context path inside the repository.

    :param repo_root: Repository root path.
    :param build_context: Build context relative path.
    :returns: Absolute build context path.
    :raises ValueError: If the build context is invalid.
    """
    context_path = (repo_root / build_context).resolve()

    try:
        context_path.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError('build context must stay within the repository root') from exc

    return context_path


def scaffold_dockerfile(image_slug: str) -> str:
    """
    Return starter Dockerfile contents for a missing build context.

    :param image_slug: Docker image slug without the namespace prefix.
    :returns: Starter Dockerfile contents.
    """
    return f'FROM {image_slug}\n'


def ensure_build_context(context_path: pathlib.Path, image_slug: str) -> list[str]:
    """
    Ensure the build context directory and Dockerfile exist.

    :param context_path: Absolute build context path.
    :param image_slug: Docker image slug without the namespace prefix.
    :returns: Descriptions of any files or directories created.
    :raises ValueError: If the existing path layout is incompatible.
    """
    created: list[str] = []

    if context_path.exists() and not context_path.is_dir():
        raise ValueError(f'build context path "{context_path.name}" is not a directory')

    if not context_path.exists():
        context_path.mkdir(parents=True)
        created.append(f'created directory {context_path.name}')

    dockerfile_path = context_path / 'Dockerfile'
    if dockerfile_path.exists() and not dockerfile_path.is_file():
        raise ValueError(f'build context "{context_path.name}" has a non-file Dockerfile entry')

    if not dockerfile_path.exists():
        dockerfile_path.write_text(scaffold_dockerfile(image_slug), encoding='utf-8')
        created.append(f'created {context_path.name}/Dockerfile')

    return created


def workflow_filename(build_context: str) -> str:
    """Return the generated workflow file name."""
    if build_context == '.':
        return 'root.yml'

    return f'{build_context.replace("/", "-")}.yml'


def full_image_name(image_slug: str) -> str:
    """Return the published Docker image name."""
    return f'{DEFAULT_DOCKERHUB_NAMESPACE}/{image_slug}'


def split_image_slug(image_slug: str) -> tuple[str, str]:
    """
    Split an image slug into repository and tag components.

    :param image_slug: Docker image slug without the namespace prefix.
    :returns: Repository name and tag.
    """
    if ':' in image_slug:
        repository, tag = image_slug.split(':', maxsplit=1)
        return repository, tag

    return image_slug, 'latest'


def workflow_name(image_slug: str) -> str:
    """Return the workflow display name."""
    return f'build {full_image_name(image_slug)}'

def build_context_path_filter(build_context: str) -> str:
    """Return the GitHub Actions path filter for the build context."""
    if build_context == '.':
        return '**'

    return f'{build_context}/**'


def workflow_support_paths() -> list[str]:
    """Return shared workflow support files that should trigger rebuilds."""
    return [
        '.github/workflows/check_readme_image.py',
    ]


def render_workflow(image_slug: str, build_context: str) -> str:
    """
    Render the GitHub Actions workflow YAML.

    :param image_slug: Docker image slug without the namespace prefix.
    :param build_context: Build context relative path.
    :returns: Workflow YAML content.
    """
    workflow_file = workflow_filename(build_context)
    image_name = full_image_name(image_slug)
    image_repository, image_tag = split_image_slug(image_slug)
    image_base = f'{DEFAULT_DOCKERHUB_NAMESPACE}/{image_repository}'
    dockerfile_path = './Dockerfile' if build_context == '.' else f'./{build_context}/Dockerfile'
    lines = [
        f'name: {workflow_name(image_slug)}',
        '',
        'on:',
        '  push:',
        '    branches: [ main ]',
        '    paths:',
    ]

    for path_filter in [f'.github/workflows/{workflow_file}', *workflow_support_paths(), build_context_path_filter(build_context)]:
        lines.append(f"      - '{path_filter}'")

    lines.extend([
        '  workflow_dispatch: {}',
        '',
        'jobs:',
        '  push_to_registry:',
        '    name: Push Docker image to Docker Hub',
        '    runs-on: ubuntu-latest',
        '    permissions:',
        '      contents: read',
        '      packages: write',
        '      attestations: write',
        '      id-token: write',
        '    steps:',
        '      - name: Check out the repo',
        '        uses: actions/checkout@v6',
        '',
        '      - name: Set image variables',
        '        id: vars',
        f'        run: echo "IMAGE={image_name}" >> "$GITHUB_OUTPUT"',
        '',
        '      - name: Verify README entry',
        '        run: python3 .github/workflows/check_readme_image.py --image "${{ steps.vars.outputs.IMAGE }}"',
        '',
        '      - name: Log in to Docker Hub',
        '        uses: docker/login-action@f4ef78c080cd8ba55a85445d5b36e214a81df20a',
        '        with:',
        '          username: ${{ secrets.REGISTRY_USER }}',
        '          password: ${{ secrets.REGISTRY_ACCESS_TOKEN }}',
        '',
        '      - name: Extract metadata (tags, labels) for Docker',
        '        id: meta',
        '        uses: docker/metadata-action@9ec57ed1fcdbf14dcef7dfbe97b2010124a938b7',
        '        with:',
        f'          images: {image_base}',
        f'          tags: type=raw,value={image_tag}',
        '',
        '      - name: Build and push Docker image',
        '        id: push',
        '        uses: docker/build-push-action@3b5e8027fcad23fda98b2e3ac259d8d67585f671',
        '        with:',
        f'          context: {build_context}',
        f'          file: {dockerfile_path}',
        '          push: true',
        '          tags: ${{ steps.meta.outputs.tags }}',
        '          labels: ${{ steps.meta.outputs.labels }}',
        '',
        '      - name: Generate artifact attestation',
        '        uses: actions/attest@v4',
        '        with:',
        f'          subject-name: index.docker.io/{image_base}',
        '          subject-digest: ${{ steps.push.outputs.digest }}',
        '          push-to-registry: true',
        '',
    ])
    return '\n'.join(lines)


def write_workflow(repo_root: pathlib.Path, build_context: str, workflow_text: str) -> pathlib.Path:
    """
    Write the generated workflow file.

    :param repo_root: Repository root path.
    :param build_context: Build context relative path.
    :param workflow_text: Workflow YAML content.
    :returns: Written workflow path.
    """
    workflow_path = repo_root / WORKFLOW_DIR / workflow_filename(build_context)
    workflow_path.write_text(workflow_text, encoding='utf-8')
    return workflow_path


def main() -> int:
    """Create a workflow file from the provided inputs."""
    args = parse_args()
    repo_root = pathlib.Path(__file__).resolve().parents[4]
    image_slug = args.image_slug.strip()
    build_context = normalize_build_context(args.build_context)

    try:
        validate_image_slug(image_slug)
        context_path = resolve_build_context(repo_root, build_context)
        created = ensure_build_context(context_path, image_slug)
        workflow_text = render_workflow(image_slug, build_context)
    except ValueError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1

    if args.dry_run:
        print(workflow_text)
        return 0

    workflow_path = write_workflow(repo_root, build_context, workflow_text)
    for item in created:
        print(item)
    print(f'Created {workflow_path.relative_to(repo_root).as_posix()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
