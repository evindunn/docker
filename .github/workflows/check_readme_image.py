#!/usr/bin/env python3
"""Fail if a Docker image entry is missing from the managed README table."""

import argparse
import pathlib
import re
import sys


README_PATH = pathlib.Path('README.md')
TABLE_END_MARKER = '<!-- docker-images-table:end -->'
TABLE_START_MARKER = '<!-- docker-images-table:start -->'


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Verify that a Docker image is documented in README.md.',
    )
    parser.add_argument(
        '--image',
        required=True,
        help='Fully qualified Docker image name expected in the README table.',
    )
    return parser.parse_args()


def managed_table(readme_text: str) -> str:
    """
    Return the managed Docker image table section from README.md.

    :param readme_text: Full README contents.
    :returns: Managed table section.
    :raises ValueError: If the table markers are missing.
    """
    pattern = re.compile(
        rf'{re.escape(TABLE_START_MARKER)}\n(?P<table>.*?)\n{re.escape(TABLE_END_MARKER)}',
        re.DOTALL,
    )
    match = pattern.search(readme_text)
    if match is None:
        raise ValueError('README.md is missing the managed Docker image table markers')

    return match.group('table')


def image_present(table_text: str, image: str) -> bool:
    """
    Return whether the given image appears in the managed README table.

    :param table_text: Managed table section from README.md.
    :param image: Fully qualified Docker image name to find.
    :returns: True when the image is present.
    """
    return f'`{image}`' in table_text


def main() -> int:
    """Validate that the requested image exists in README.md."""
    args = parse_args()

    try:
        readme_text = README_PATH.read_text(encoding='utf-8')
        table_text = managed_table(readme_text)
    except (OSError, ValueError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1

    if not image_present(table_text, args.image):
        print(
            f'error: image "{args.image}" is not documented in README.md',
            file=sys.stderr,
        )
        return 1

    print(f'Confirmed README.md documents {args.image}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
