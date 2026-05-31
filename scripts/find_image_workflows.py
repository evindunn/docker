#!/usr/bin/env python3
"""Print workflow names that build the provided images."""

import argparse
import json
import pathlib
import sys


DEFAULT_TAG = 'latest'
WORKFLOW_NAME_PREFIX = 'name: build '
WORKFLOWS_DIR = pathlib.Path(__file__).resolve().parent.parent / '.github' / 'workflows'


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Print a JSON list of workflow names that build the provided images from JSON or stdin.',
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


def normalize_image(image: str) -> str:
    """
    Return a comparable image reference with an explicit tag.

    :param image: Image reference, with or without a tag.
    :returns: Normalized image reference.
    """
    if ':' in image:
        return image

    return f'{image}:{DEFAULT_TAG}'


def workflow_name(workflow_path: pathlib.Path, images: set[str]) -> str | None:
    """
    Return the workflow name when it builds one of the provided images.

    :param workflow_path: Workflow file to inspect.
    :param images: Published image references to match.
    :returns: Workflow display name when it matches, otherwise ``None``.
    """
    for raw_line in workflow_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line.startswith(WORKFLOW_NAME_PREFIX):
            continue

        workflow_image = normalize_image(line.removeprefix(WORKFLOW_NAME_PREFIX))
        if workflow_image in images:
            return line.removeprefix('name:').strip()
        return None

    return None


def find_workflow_names(images: list[str]) -> list[str]:
    """
    Find workflow names that build the provided images.

    :param images: Published image references to match.
    :returns: Sorted list of matching workflow names.
    """
    normalized_images = {normalize_image(image) for image in images}
    matches: set[str] = set()

    for workflow_path in sorted(WORKFLOWS_DIR.glob('*.yml')):
        match = workflow_name(workflow_path, normalized_images)
        if match is not None:
            matches.add(match)

    return sorted(matches)


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

    json.dump(find_workflow_names(images), sys.stdout)
    sys.stdout.write('\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
