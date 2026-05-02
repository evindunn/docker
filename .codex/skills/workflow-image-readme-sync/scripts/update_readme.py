#!/usr/bin/env python3
"""Update README.md with Docker images discovered in workflow files."""

import dataclasses
import pathlib
import re
import sys


README_PATH = pathlib.Path('README.md')
TABLE_END_MARKER = '<!-- docker-images-table:end -->'
TABLE_START_MARKER = '<!-- docker-images-table:start -->'
WORKFLOW_DIR = pathlib.Path('.github/workflows')
WORKFLOW_GLOBS = ('*.yml', '*.yaml')
BUILD_CONTEXT_PATTERN = re.compile(
    r'docker\s+build(?:x)?(?:\s+[^\n]*)?\s+(?P<context>\.[A-Za-z0-9._/-]*|[A-Za-z0-9._/-]+)\s*$',
    re.MULTILINE,
)
COPY_CERTIFICATE_PATTERN = re.compile(r'COPY\s+([^\n]+\.crt)\b', re.IGNORECASE)
DOCKERFILE_FROM_PATTERN = re.compile(
    r'^\s*FROM\s+(?P<image>[^\s]+)',
    re.IGNORECASE | re.MULTILINE,
)
INSTALL_PACKAGES_PATTERN = re.compile(
    r'apt(?:-get)?\s+install\s+-y\s+(?P<packages>.+?)(?:\n\s*(?:&&|RUN|COPY|FROM)\b|$)',
    re.IGNORECASE | re.DOTALL,
)
WORKFLOW_IMAGE_PATTERNS = (
    re.compile(r'IMAGE\s*=\s*(?P<image>[A-Za-z0-9._/-]+(?::[A-Za-z0-9._-]+)?)'),
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
                build_image_record(repo_root, workflow_path, context_dir, image),
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
            image = match.group('image')
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

    return None


def build_image_record(
    repo_root: pathlib.Path,
    workflow_path: pathlib.Path,
    context_dir: pathlib.Path | None,
    image: str,
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
    description = 'Docker image published by this repository.'

    if dockerfile_path is not None and dockerfile_path.is_file():
        dockerfile_text = dockerfile_path.read_text(encoding='utf-8')
        base_image = infer_base_image(dockerfile_text)
        context_name = context_dir.relative_to(repo_root).as_posix()
        description = infer_description(
            repo_root=repo_root,
            context_dir=context_dir,
            dockerfile_text=dockerfile_text,
        )
    elif context_dir is not None and context_dir.is_dir():
        context_name = context_dir.relative_to(repo_root).as_posix()
        description = 'Docker image published by this repository.'

    return ImageRecord(
        image=image,
        base_image=base_image,
        context=context_name,
        workflow=workflow_name,
        description=description,
    )


def infer_base_image(dockerfile_text: str) -> str:
    """Infer the base image from a Dockerfile."""
    match = DOCKERFILE_FROM_PATTERN.search(dockerfile_text)
    if match is None:
        return 'Unknown'

    return match.group('image')


def infer_description(
    repo_root: pathlib.Path,
    context_dir: pathlib.Path,
    dockerfile_text: str,
) -> str:
    """
    Infer a human-readable description from the build context.

    :param repo_root: Repository root path.
    :param context_dir: Build context directory.
    :param dockerfile_text: Dockerfile contents.
    :returns: Human-readable description for README.md.
    """
    packages = infer_installed_packages(dockerfile_text)
    copied_certificates = infer_copied_certificates(dockerfile_text)
    description_parts: list[str] = []

    if packages:
        description_parts.append(f'adds `{", ".join(packages)}`')

    if copied_certificates:
        certificate_phrase = 'certificate' if len(copied_certificates) == 1 else 'certificates'
        description_parts.append(
            f'installs local CA {certificate_phrase} from `{", ".join(copied_certificates)}`'
        )

    if not description_parts:
        return 'Docker image published by this repository.'

    return f'Docker image that {join_description_parts(description_parts)}.'


def infer_installed_packages(dockerfile_text: str) -> list[str]:
    """Infer installed APT packages from a Dockerfile."""
    packages: list[str] = []

    for match in INSTALL_PACKAGES_PATTERN.finditer(dockerfile_text):
        raw_packages = match.group('packages')
        for token in raw_packages.replace('\\', ' ').split():
            if token.startswith('-'):
                continue
            if token in {'&&', 'apt', 'apt-get', 'install', 'RUN'}:
                continue
            if token not in packages:
                packages.append(token)

    return packages


def infer_copied_certificates(dockerfile_text: str) -> list[str]:
    """Infer copied certificate files from a Dockerfile."""
    certificates: list[str] = []

    for match in COPY_CERTIFICATE_PATTERN.finditer(dockerfile_text):
        certificate_path = pathlib.Path(match.group(1)).name
        if certificate_path not in certificates:
            certificates.append(certificate_path)

    return certificates


def join_description_parts(description_parts: list[str]) -> str:
    """Join description fragments into a readable English phrase."""
    if len(description_parts) == 1:
        return description_parts[0]

    return f'{", ".join(description_parts[:-1])}, and {description_parts[-1]}'


def dockerhub_url(image: str) -> str:
    """Return the Docker Hub URL for an image reference."""
    repository = image.split(':', maxsplit=1)[0]
    return f'https://hub.docker.com/r/{repository}'


def render_context(context: str) -> str:
    """Render the context column as a local Markdown link when available."""
    if context == 'Unknown':
        return context

    return f'[{context}]({context})'


def render_workflow(workflow: str) -> str:
    """Render the workflow column as a local Markdown link when available."""
    if workflow == 'Unknown':
        return workflow

    return f'[{workflow}]({workflow})'


def render_table(images: list[ImageRecord]) -> str:
    """Render the README table for discovered images."""
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
                f'{render_workflow(image_record.workflow)} | '
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

    try:
        images = discover_images(repo_root)
        table = render_table(images)
        update_readme(repo_root, table)
    except Exception as exc:  # pragma: no cover - CLI error path
        print(f'error: {exc}', file=sys.stderr)
        return 1

    print(f'Updated README.md with {len(images)} discovered Docker image(s).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
