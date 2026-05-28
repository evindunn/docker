#!/usr/bin/env python3
"""Print workflow names whose build contexts use a given base image."""

import argparse
import json
import pathlib
import re
import sys


DOCKERFILE_GLOB = 'Dockerfile*'
FROM_LINE_RE = re.compile(r'^FROM(?:\s+--platform=\S+)?\s+(?P<image>\S+)(?:\s+AS\s+\S+)?$', re.IGNORECASE)
WORKFLOW_CONTEXT_RE = re.compile(r'^\s*context:\s*(?:"(?P<quoted>[^"]+)"|(?P<plain>\S+))\s*$')
WORKFLOW_NAME_RE = re.compile(r'^name:\s*(?P<name>.+?)\s*$')
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / '.github' / 'workflows'


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Print a JSON list of workflow names whose build contexts use the given base image.',
    )
    parser.add_argument(
        'image',
        help='Base image reference to match, for example evindunn/debian:trixie-slim.',
    )
    return parser.parse_args()


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


def workflow_name_for_context(context: str, workflow_path: pathlib.Path) -> str | None:
    """
    Return the workflow display name when the workflow builds the provided context.

    :param context: Build context to match.
    :param workflow_path: Workflow file to inspect.
    :returns: Workflow name when the context matches, otherwise ``None``.
    """
    workflow_name: str | None = None
    workflow_context: str | None = None

    for raw_line in workflow_path.read_text(encoding='utf-8').splitlines():
        if workflow_name is None:
            workflow_name_match = WORKFLOW_NAME_RE.match(raw_line)
            if workflow_name_match:
                workflow_name = workflow_name_match.group('name').strip()
                continue

        workflow_context_match = WORKFLOW_CONTEXT_RE.match(raw_line)
        if workflow_context_match:
            workflow_context = workflow_context_match.group('quoted') or workflow_context_match.group('plain')

    if workflow_name and workflow_context == context:
        return workflow_name

    return None


def find_workflow_names(image: str) -> list[str]:
    """
    Find workflow names that build contexts using the provided base image.

    :param image: Exact image reference to match.
    :returns: Sorted list of unique workflow names.
    """
    build_contexts = set(find_build_contexts(image))
    workflow_names: set[str] = set()

    for workflow_path in sorted(WORKFLOWS_DIR.glob('*.yml')):
        for context in build_contexts:
            workflow_name = workflow_name_for_context(context, workflow_path)
            if workflow_name is not None:
                workflow_names.add(workflow_name)

    return sorted(workflow_names)


def main() -> int:
    """Run the command-line interface."""
    args = parse_args()
    json.dump(find_workflow_names(args.image), sys.stdout)
    sys.stdout.write('\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
