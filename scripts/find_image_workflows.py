#!/usr/bin/env python3
"""Print workflow names that build a given published image."""

import argparse
import json
import pathlib
import re
import sys


DEFAULT_TAG = 'latest'
WORKFLOW_NAME_RE = re.compile(r'^name:\s*build\s+(?P<image>\S+)\s*$')
WORKFLOWS_DIR = pathlib.Path(__file__).resolve().parent.parent / '.github' / 'workflows'


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Print a JSON list of workflow names that build the provided image.',
    )
    parser.add_argument(
        'image',
        help='Published image reference to match, for example evindunn/debian:trixie-slim.',
    )
    return parser.parse_args()


def normalize_image(image: str) -> str:
    """
    Return a comparable image reference with an explicit tag.

    :param image: Image reference, with or without a tag.
    :returns: Normalized image reference.
    """
    if ':' in image:
        return image

    return f'{image}:{DEFAULT_TAG}'


def workflow_name(workflow_path: pathlib.Path, image: str) -> str | None:
    """
    Return the workflow name when it builds the provided image.

    :param workflow_path: Workflow file to inspect.
    :param image: Published image reference to match.
    :returns: Workflow display name when it matches, otherwise ``None``.
    """
    for raw_line in workflow_path.read_text(encoding='utf-8').splitlines():
        match = WORKFLOW_NAME_RE.match(raw_line.strip())
        if match is None:
            continue

        workflow_image = normalize_image(match.group('image'))
        if workflow_image == normalize_image(image):
            return raw_line.removeprefix('name:').strip()
        return None

    return None


def find_workflow_names(image: str) -> list[str]:
    """
    Find workflow names that build the provided image.

    :param image: Published image reference to match.
    :returns: Sorted list of matching workflow names.
    """
    matches: set[str] = set()

    for workflow_path in sorted(WORKFLOWS_DIR.glob('*.yml')):
        match = workflow_name(workflow_path, image)
        if match is not None:
            matches.add(match)

    return sorted(matches)


def main() -> int:
    """Run the command-line interface."""
    args = parse_args()
    json.dump(find_workflow_names(args.image), sys.stdout)
    sys.stdout.write('\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
