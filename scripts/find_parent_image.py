#!/usr/bin/env python3
"""Print the base image used by a build context Dockerfile."""

import argparse
import pathlib
import re
import sys


DOCKERFILE_NAME = 'Dockerfile'
FROM_LINE_RE = re.compile(r'^FROM(?:\s+--platform=\S+)?\s+(?P<image>\S+)(?:\s+AS\s+\S+)?$', re.IGNORECASE)
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Print the base image used by the Dockerfile in the provided build context.',
    )
    parser.add_argument(
        'context',
        help='Build context directory relative to the repository root.',
    )
    return parser.parse_args()


def dockerfile_path_for_context(context: str) -> pathlib.Path:
    """
    Return the Dockerfile path for the provided build context.

    :param context: Build context directory relative to the repository root.
    :returns: Absolute Dockerfile path.
    :raises ValueError: If the context resolves outside the repository or lacks a Dockerfile.
    """
    context_path = (REPO_ROOT / context).resolve()

    try:
        context_path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise ValueError('build context must stay within the repository root') from exc

    dockerfile_path = context_path / DOCKERFILE_NAME
    if not dockerfile_path.is_file():
        raise ValueError(f'no Dockerfile found for build context "{context}"')

    return dockerfile_path


def find_parent_image(context: str) -> str:
    """
    Return the last base image from the build context Dockerfile.

    :param context: Build context directory relative to the repository root.
    :returns: Base image reference from the last ``FROM`` instruction.
    :raises ValueError: If the Dockerfile has no supported ``FROM`` instruction.
    """
    dockerfile_path = dockerfile_path_for_context(context)
    parent_image: str | None = None

    for raw_line in dockerfile_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue

        match = FROM_LINE_RE.match(line)
        if match:
            parent_image = match.group('image')

    if parent_image is not None:
        return parent_image

    raise ValueError(f'no supported FROM instruction found in "{dockerfile_path.relative_to(REPO_ROOT)}"')


def main() -> int:
    """Run the command-line interface."""
    args = parse_args()

    try:
        print(find_parent_image(args.context))
    except ValueError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
