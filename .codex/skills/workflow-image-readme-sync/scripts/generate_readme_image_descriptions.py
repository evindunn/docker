#!/usr/bin/env python3
"""Generate README image descriptions by invoking the ai-tooling CLI."""

import argparse
import json
import pathlib
import subprocess
import sys

import update_readme


DEFAULT_MODEL = 'gpt-5-mini'


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate README image descriptions for discovered Docker images.',
    )
    parser.add_argument(
        '--model',
        default=DEFAULT_MODEL,
        help='OpenAI model to pass through to generate-image-description.',
    )
    parser.add_argument(
        '--output',
        required=True,
        type=pathlib.Path,
        help='Path to the JSON file that will receive image descriptions.',
    )
    return parser.parse_args()


def generate_description(
    repo_root: pathlib.Path,
    context_path: pathlib.Path,
    model: str,
) -> str:
    """
    Generate a README description for a Docker build context.

    :param repo_root: Repository root path.
    :param context_path: Absolute path to the Docker build context directory.
    :param model: OpenAI model name for the CLI invocation.
    :returns: Generated description string.
    :raises ValueError: If the CLI fails or returns invalid JSON.
    """
    result = subprocess.run(
        [
            'generate-image-description',
            context_path.relative_to(repo_root).as_posix(),
            '--model',
            model,
        ],
        check=False,
        capture_output=True,
        cwd=repo_root,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or 'unknown error'
        raise ValueError(
            f'generate-image-description failed for {context_path.relative_to(repo_root).as_posix()}: {stderr}',
        )

    try:
        response_data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f'generate-image-description returned invalid JSON for '
            f'{context_path.relative_to(repo_root).as_posix()}: {exc}'
        ) from exc

    description = response_data.get('description')
    if not isinstance(description, str):
        raise ValueError(
            f'generate-image-description did not return a string description for '
            f'{context_path.relative_to(repo_root).as_posix()}'
        )

    return description


def main() -> int:
    """Generate descriptions for all discovered README image rows."""
    args = parse_args()
    repo_root = pathlib.Path(__file__).resolve().parents[4]

    try:
        images = update_readme.discover_images(repo_root)
        descriptions: dict[str, str] = {}
        descriptions_by_context: dict[str, str] = {}

        for image_record in images:
            if image_record.context == 'Unknown':
                raise ValueError(f'cannot generate description for {image_record.image} without a build context')

            context_path = repo_root / image_record.context
            context_key = context_path.as_posix()
            if context_key not in descriptions_by_context:
                descriptions_by_context[context_key] = generate_description(repo_root, context_path, args.model)
            descriptions[image_record.image] = descriptions_by_context[context_key]

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(descriptions, indent=2, sort_keys=True), encoding='utf-8')
    except Exception as exc:  # pragma: no cover - CLI error path
        print(f'error: {exc}', file=sys.stderr)
        return 1

    print(f'Wrote {len(descriptions)} README image description(s) to {args.output}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
