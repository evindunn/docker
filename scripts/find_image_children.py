#!/usr/bin/env python3
"""Print child image references built from a given parent image."""

import argparse
import json
import pathlib
import re
import sys


DOCKERFILE_GLOB = 'Dockerfile*'
FROM_LINE_RE = re.compile(r'^FROM(?:\s+--platform=\S+)?\s+(?P<image>\S+)(?:\s+AS\s+\S+)?$', re.IGNORECASE)
WORKFLOW_CONTEXT_RE = re.compile(r'^\s*context:\s*(?:"(?P<quoted>[^"]+)"|(?P<plain>\S+))\s*$')
WORKFLOW_NAME_RE = re.compile(r'^name:\s*build\s+(?P<image>\S+)\s*$')
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / '.github' / 'workflows'


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Print a JSON list of child image references built from the provided base image from JSON or stdin.',
    )
    parser.add_argument(
        'images_json',
        nargs='?',
        help='A single image reference or a JSON array of image references to match',
    )
    return parser.parse_args()


def parse_images_input(images_json: str) -> list[str]:
    """
    Parse a JSON array of image references. If images_json is a single string,
    it will be treated as a one-element array.

    :param images_json: JSON text representing a list of image references.
    :returns: Parsed image references.
    :raises ValueError: If the input is not a JSON array of strings.
    """
    try:
        parsed_images = json.loads(images_json)
    except json.JSONDecodeError:
        parsed_images = [images_json.strip()]

    if not parsed_images:
        raise ValueError('input must contain at least one image reference')

    if not all(isinstance(image, str) for image in parsed_images):
        raise ValueError('input must be a JSON array of strings')

    return parsed_images


def dockerfile_context(dockerfile_path: pathlib.Path) -> str:
    """Return the build context path for a Dockerfile."""
    relative_parent = dockerfile_path.parent.relative_to(REPO_ROOT)
    context = relative_parent.as_posix()
    return context or '.'


def dockerfile_uses_base_image(dockerfile_path: pathlib.Path, image: str) -> bool:
    """
    Return whether the Dockerfile uses the provided image in a FROM instruction.

    :param dockerfile_path: Path to the Dockerfile to inspect.
    :param image: Exact image reference to match.
    :returns: ``True`` when the Dockerfile uses the image as a base.
    """
    for raw_line in dockerfile_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue

        match = FROM_LINE_RE.match(line)
        if match and match.group('image') == image:
            return True

    return False


def find_build_contexts(image: str) -> list[str]:
    """
    Find build contexts whose Dockerfiles use the provided base image.

    :param image: Exact image reference to match.
    :returns: Sorted list of unique build-context paths.
    """
    matches: set[str] = set()

    for dockerfile_path in sorted(REPO_ROOT.glob(f'*/{DOCKERFILE_GLOB}')):
        if dockerfile_uses_base_image(dockerfile_path, image):
            matches.add(dockerfile_context(dockerfile_path))

    return sorted(matches)


def workflow_image_for_context(context: str, workflow_path: pathlib.Path) -> str | None:
    """
    Return the published image reference when the workflow builds the provided context.

    :param context: Build context to match.
    :param workflow_path: Workflow file to inspect.
    :returns: Published image reference when the context matches, otherwise ``None``.
    """
    workflow_context: str | None = None
    workflow_image: str | None = None

    for raw_line in workflow_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if workflow_image is None:
            match = WORKFLOW_NAME_RE.match(line)
            if match is not None:
                workflow_image = match.group('image')
                continue

        workflow_context_match = WORKFLOW_CONTEXT_RE.match(raw_line)
        if workflow_context_match:
            workflow_context = workflow_context_match.group('quoted') or workflow_context_match.group('plain')

    if workflow_image and workflow_context == context:
        return workflow_image

    return None


def find_child_images(image: str) -> list[str]:
    """
    Find child image references built from the provided image.

    :param image: Base image reference to match.
    :returns: Sorted list of matching child image references.
    """
    build_contexts = set(find_build_contexts(image))
    workflow_images: set[str] = set()

    for workflow_path in sorted(WORKFLOWS_DIR.glob('*.yml')):
        for context in build_contexts:
            workflow_image = workflow_image_for_context(context, workflow_path)
            if workflow_image is not None:
                workflow_images.add(workflow_image)

    return sorted(workflow_images)


def main() -> int:
    """Run the command-line interface."""
    args = parse_args()

    images_json = args.images_json
    if images_json is None:
        if sys.stdin.isatty():
            print('error: expected a JSON array or single string as input', file=sys.stderr)
            return 1
        else:
            images_json = sys.stdin.read()

    try:
        images = parse_images_input(images_json)
    except ValueError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1

    child_images: set[str] = set()
    for image in images:
        child_images.update(find_child_images(image))

    json.dump(sorted(child_images), sys.stdout)
    sys.stdout.write('\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
