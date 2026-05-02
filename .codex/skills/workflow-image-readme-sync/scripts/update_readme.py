#!/usr/bin/env python3
"""Update README.md with Docker images discovered in workflow files."""

import dataclasses
import json
import pathlib
import re
import subprocess
import sys


DEFAULT_GITHUB_REPOSITORY = 'evindunn/docker'
README_PATH = pathlib.Path('README.md')
TABLE_END_MARKER = '<!-- docker-images-table:end -->'
TABLE_START_MARKER = '<!-- docker-images-table:start -->'
WORKFLOW_DIR = pathlib.Path('.github/workflows')
WORKFLOW_GLOBS = ('*.yml', '*.yaml')
BUILD_CONTEXT_PATTERN = re.compile(
    r'docker\s+build(?:x)?(?:\s+[^\n]*)?\s+(?P<context>\.[A-Za-z0-9._/-]*|[A-Za-z0-9._/-]+)\s*$',
    re.MULTILINE,
)
BUILD_PUSH_CONTEXT_PATTERN = re.compile(r'^\s*context:\s*(?P<context>[A-Za-z0-9._/-]+)\s*$', re.MULTILINE)
WORKFLOW_INPUT_CONTEXT_PATTERN = re.compile(r'^\s*context:\s*(?P<context>[A-Za-z0-9._/-]+)\s*$', re.MULTILINE)
COPY_CERTIFICATE_PATTERN = re.compile(r'COPY\s+([^\n]+\.crt)\b', re.IGNORECASE)
DOCKERFILE_FROM_PATTERN = re.compile(
    r'^\s*FROM\s+(?P<image>[^\s]+)',
    re.IGNORECASE | re.MULTILINE,
)
DOWNLOAD_BINARY_PATTERN = re.compile(r'(?P<path>/[A-Za-z0-9._/-]+)', re.IGNORECASE)
ENTRYPOINT_PATTERN = re.compile(r'^\s*ENTRYPOINT\s+\[(?P<entrypoint>[^\]]+)\]', re.MULTILINE)
GITHUB_REMOTE_PATTERN = re.compile(r'github\.com[:/](?P<slug>[^/]+/[^/.]+?)(?:\.git)?$')
USER_PATTERN = re.compile(r'^\s*USER\s+(?P<user>[A-Za-z0-9._-]+)\s*$', re.MULTILINE)
WORKFLOW_IMAGE_PATTERNS = (
    re.compile(r'IMAGE\s*=\s*(?P<image>[A-Za-z0-9._/-]+(?::[A-Za-z0-9._-]+)?)'),
    re.compile(
        r'^\s*image:\s*(?P<repository>[A-Za-z0-9._/-]+)\s*$\n^\s*tag:\s*(?P<tag>[A-Za-z0-9._-]+)\s*$',
        re.MULTILINE,
    ),
    re.compile(
        r'images:\s*(?P<repository>[A-Za-z0-9._/-]+)\s*\n\s*tags:\s*type=raw,value=(?P<tag>[A-Za-z0-9._-]+)',
        re.MULTILINE,
    ),
    re.compile(r'docker\s+build(?:x)?(?:\s+[^\n]*)?\s+-t\s+(?P<image>[A-Za-z0-9._/-]+(?::[A-Za-z0-9._-]+)?)'),
    re.compile(r'docker\s+push\s+(?P<image>[A-Za-z0-9._/-]+(?::[A-Za-z0-9._-]+)?)'),
)


@dataclasses.dataclass(frozen=True)
class ImageRecord:
    """
    Docker image metadata rendered into README.md.

    :param image: Published Docker image reference.
    :param base_image: Base image reference from the build context Dockerfile.
    :param context: Build context path for the image.
    :param workflow: Workflow path that builds and publishes the image.
    :param description: Human-readable description for the image.
    """

    image: str
    base_image: str
    context: str
    workflow: str
    description: str


def parse_args() -> tuple[pathlib.Path | None, bool]:
    """Parse command-line arguments."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Discover Docker images from workflows and render the README table.',
    )
    parser.add_argument(
        '--description-file',
        help='JSON file mapping full image names to human-written descriptions.',
    )
    parser.add_argument(
        '--print-discovery-json',
        action='store_true',
        help='Print discovered image metadata as JSON instead of updating README.md.',
    )
    args = parser.parse_args()

    description_path = None if args.description_file is None else pathlib.Path(args.description_file)
    return description_path, args.print_discovery_json


def discover_images(repo_root: pathlib.Path) -> list[ImageRecord]:
    """Return discovered Docker images with inferred metadata."""
    images: dict[str, ImageRecord] = {}
    workflow_dir = repo_root / WORKFLOW_DIR

    for workflow_path in sorted(iter_workflow_files(workflow_dir)):
        workflow_text = workflow_path.read_text(encoding='utf-8')
        context_dir = resolve_context_dir(repo_root, workflow_path, workflow_text)
        for image in extract_images(workflow_text):
            images.setdefault(
                image,
                build_image_record(repo_root, workflow_path, context_dir, image, None),
            )

    return sorted(images.values(), key=lambda record: record.image)


def iter_workflow_files(workflow_dir: pathlib.Path) -> list[pathlib.Path]:
    """Return workflow files using the supported glob patterns."""
    workflow_files: list[pathlib.Path] = []

    for pattern in WORKFLOW_GLOBS:
        workflow_files.extend(sorted(workflow_dir.glob(pattern)))

    return workflow_files


def extract_images(workflow_text: str) -> list[str]:
    """Extract Docker image references from workflow text."""
    images: list[str] = []

    for pattern in WORKFLOW_IMAGE_PATTERNS:
        for match in pattern.finditer(workflow_text):
            if 'image' in match.groupdict():
                image = match.group('image')
            else:
                image = f"{match.group('repository')}:{match.group('tag')}"
            if image not in images:
                images.append(image)

    return images


def resolve_context_dir(
    repo_root: pathlib.Path,
    workflow_path: pathlib.Path,
    workflow_text: str,
) -> pathlib.Path | None:
    """
    Resolve the Docker build context directory for a workflow.

    :param repo_root: Repository root path.
    :param workflow_path: Workflow file where the image was discovered.
    :param workflow_text: Raw workflow contents.
    :returns: Build context directory when one can be determined.
    """
    workflow_stem_dir = repo_root / workflow_path.stem
    if workflow_stem_dir.is_dir():
        return workflow_stem_dir

    match = BUILD_CONTEXT_PATTERN.search(workflow_text)
    if match:
        context_value = match.group('context')
        if context_value == '.':
            return repo_root

        context_path = (repo_root / context_value).resolve()
        if context_path.is_dir():
            return context_path

    match = BUILD_PUSH_CONTEXT_PATTERN.search(workflow_text)
    if match:
        context_value = match.group('context')
        if context_value == '.':
            return repo_root

        context_path = (repo_root / context_value).resolve()
        if context_path.is_dir():
            return context_path

    match = WORKFLOW_INPUT_CONTEXT_PATTERN.search(workflow_text)
    if match:
        context_value = match.group('context')
        if context_value == '.':
            return repo_root

        context_path = (repo_root / context_value).resolve()
        if context_path.is_dir():
            return context_path

    return None


def build_image_record(
    repo_root: pathlib.Path,
    workflow_path: pathlib.Path,
    context_dir: pathlib.Path | None,
    image: str,
    description: str | None,
) -> ImageRecord:
    """
    Build metadata for a discovered image.

    :param repo_root: Repository root path.
    :param workflow_path: Workflow file where the image was discovered.
    :param context_dir: Build context directory for the image, when known.
    :param image: Docker image reference.
    :returns: Metadata record for README.md.
    """
    workflow_name = workflow_path.relative_to(repo_root).as_posix()
    dockerfile_path = None if context_dir is None else context_dir / 'Dockerfile'
    base_image = 'Unknown'
    context_name = 'Unknown'
    image_description = default_description(context_dir)

    if dockerfile_path is not None and dockerfile_path.is_file():
        dockerfile_text = dockerfile_path.read_text(encoding='utf-8')
        base_image = infer_base_image(dockerfile_text)
        context_name = context_dir.relative_to(repo_root).as_posix()
    elif context_dir is not None and context_dir.is_dir():
        context_name = context_dir.relative_to(repo_root).as_posix()

    return ImageRecord(
        image=image,
        base_image=base_image,
        context=context_name,
        workflow=workflow_name,
        description=image_description if description is None else description,
    )

def infer_base_image(dockerfile_text: str) -> str:
    """Infer the base image from a Dockerfile."""
    match = DOCKERFILE_FROM_PATTERN.search(dockerfile_text)
    if match is None:
        return 'Unknown'

    return match.group('image')


def default_description(context_dir: pathlib.Path | None) -> str:
    """Return a placeholder description for agent-first authoring."""
    if context_dir is None:
        return 'TODO: add description'

    return f'TODO: add description for {context_dir.name}'


def dockerhub_url(image: str) -> str:
    """Return the Docker Hub URL for an image reference."""
    repository = image.split(':', maxsplit=1)[0]
    return f'https://hub.docker.com/r/{repository}'


def render_context(context: str) -> str:
    """Render the context column as a local Markdown link when available."""
    if context == 'Unknown':
        return context

    return f'[{context}]({context})'


def github_repository_slug(repo_root: pathlib.Path) -> str:
    """
    Return the GitHub repository slug for workflow badge URLs.

    :param repo_root: Repository root path.
    :returns: GitHub repository slug in ``owner/name`` form.
    """
    try:
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            check=True,
            capture_output=True,
            cwd=repo_root,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return DEFAULT_GITHUB_REPOSITORY

    match = GITHUB_REMOTE_PATTERN.search(result.stdout.strip())
    if match is None:
        return DEFAULT_GITHUB_REPOSITORY

    return match.group('slug')


def render_workflow(workflow: str, repo_slug: str) -> str:
    """
    Render the workflow column as a GitHub Actions badge link when available.

    :param workflow: Repository-relative workflow path.
    :param repo_slug: GitHub repository slug in ``owner/name`` form.
    :returns: Markdown badge link for the workflow.
    """
    if workflow == 'Unknown':
        return workflow

    workflow_name = pathlib.Path(workflow).name
    workflow_url = f'https://github.com/{repo_slug}/actions/workflows/{workflow_name}'
    badge_url = f'{workflow_url}/badge.svg'
    return f'[![{workflow_name} build status]({badge_url})]({workflow_url})'


def image_record_to_dict(image_record: ImageRecord) -> dict[str, str]:
    """Convert an image record into a JSON-serializable dictionary."""
    return {
        'image': image_record.image,
        'base_image': image_record.base_image,
        'context': image_record.context,
        'workflow': image_record.workflow,
        'description': image_record.description,
    }


def load_descriptions(description_path: pathlib.Path | None) -> dict[str, str]:
    """Load image descriptions from a JSON file."""
    if description_path is None:
        return {}

    description_data = json.loads(description_path.read_text(encoding='utf-8'))
    if not isinstance(description_data, dict):
        raise ValueError('description file must contain a JSON object')

    descriptions: dict[str, str] = {}
    for image, description in description_data.items():
        if not isinstance(image, str) or not isinstance(description, str):
            raise ValueError('description file entries must map strings to strings')
        descriptions[image] = description

    return descriptions


def render_table(images: list[ImageRecord], repo_slug: str) -> str:
    """
    Render the README table for discovered images.

    :param images: Discovered image metadata.
    :param repo_slug: GitHub repository slug in ``owner/name`` form.
    :returns: Rendered Markdown table.
    """
    lines = [
        '| Image | Base Image | Context | Workflow | Description |',
        '| --- | --- | --- | --- | --- |',
    ]

    if not images:
        lines.append('| None | Unknown | Unknown | Unknown | No Docker images were discovered in `.github/workflows`. |')
    else:
        for image_record in images:
            lines.append(
                f'| [`{image_record.image}`]({dockerhub_url(image_record.image)}) | '
                f'`{image_record.base_image}` | '
                f'{render_context(image_record.context)} | '
                f'{render_workflow(image_record.workflow, repo_slug)} | '
                f'{image_record.description} |'
            )

    return '\n'.join(lines)


def update_readme(repo_root: pathlib.Path, table: str) -> None:
    """
    Replace the README table content between the managed markers.

    :param repo_root: Repository root path.
    :param table: Rendered Markdown table content.
    :raises ValueError: If the markers are missing or malformed.
    """
    readme_path = repo_root / README_PATH
    readme_text = readme_path.read_text(encoding='utf-8')
    pattern = re.compile(
        rf'({re.escape(TABLE_START_MARKER)}\n)(.*?)(\n{re.escape(TABLE_END_MARKER)})',
        re.DOTALL,
    )
    updated_text, replacements = pattern.subn(rf'\1{table}\3', readme_text, count=1)

    if replacements != 1:
        raise ValueError('README.md is missing the Docker image table markers.')

    readme_path.write_text(updated_text + ('' if updated_text.endswith('\n') else '\n'), encoding='utf-8')


def main() -> int:
    """Run the README synchronization workflow."""
    repo_root = pathlib.Path(__file__).resolve().parents[4]
    description_path, print_discovery_json = parse_args()

    try:
        images = discover_images(repo_root)
        descriptions = load_descriptions(description_path)
        repo_slug = github_repository_slug(repo_root)
        images = [
            dataclasses.replace(image_record, description=descriptions.get(image_record.image, image_record.description))
            for image_record in images
        ]
        if print_discovery_json:
            print(json.dumps([image_record_to_dict(image_record) for image_record in images], indent=2))
            return 0
        table = render_table(images, repo_slug)
        update_readme(repo_root, table)
    except Exception as exc:  # pragma: no cover - CLI error path
        print(f'error: {exc}', file=sys.stderr)
        return 1

    print(f'Updated README.md with {len(images)} discovered Docker image(s).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
