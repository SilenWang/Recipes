#!/usr/bin/env python3
"""Update doltlite/recipe.yaml to the latest doltlite release on PyPI.

rattler-build's `bump-recipe` cannot discover versions behind
files.pythonhosted.org URLs, so this script resolves the three platform
wheels (and their SHA256 checksums) from the PyPI JSON API and rewrites
the matching context variables in recipe.yaml.

Run through pixi: `pixi run update`.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

PYPI_JSON = "https://pypi.org/pypi/doltlite/json"
RECIPE = Path(__file__).with_name("recipe.yaml")

# conda platform -> (wheel filename fragment, arch fragment, context variable suffix)
PLATFORMS = {
    "linux-64": ("manylinux", "x86_64", "linux_64"),
    "linux-aarch64": ("manylinux", "aarch64", "linux_aarch64"),
    "osx-arm64": ("macosx", "arm64", "osx_arm64"),
}


def fetch_release() -> dict:
    with urllib.request.urlopen(PYPI_JSON, timeout=60) as response:
        return json.load(response)


def pick_wheels(release: dict) -> dict[str, dict]:
    wheels = {}
    files = [f for f in release["urls"] if f["packagetype"] == "bdist_wheel"]
    for platform, (platform_tag, arch, _) in PLATFORMS.items():
        matches = [
            f
            for f in files
            if platform_tag in f["filename"] and arch in f["filename"]
        ]
        if len(matches) != 1:
            raise SystemExit(
                f"expected exactly one {platform} wheel, got "
                f"{[f['filename'] for f in matches]}"
            )
        wheels[platform] = matches[0]
    return wheels


def replace_var(text: str, name: str, value: str) -> str:
    pattern = rf"(?m)^  {re.escape(name)}: .*$"
    if not re.search(pattern, text):
        raise SystemExit(f"context variable {name!r} not found in {RECIPE}")
    return re.sub(pattern, f"  {name}: {value}", text, count=1)


def main() -> int:
    release = fetch_release()
    version = release["info"]["version"]
    wheels = pick_wheels(release)

    text = RECIPE.read_text(encoding="utf-8")
    text = replace_var(text, "version", version)
    for platform, wheel in wheels.items():
        suffix = PLATFORMS[platform][2]
        text = replace_var(text, f"wheel_{suffix}", wheel["url"])
        text = replace_var(text, f"sha256_{suffix}", wheel["digests"]["sha256"])

    if RECIPE.read_text(encoding="utf-8") == text:
        print(f"doltlite {version} is already pinned in {RECIPE}")
    else:
        RECIPE.write_text(text, encoding="utf-8")
        print(f"updated {RECIPE} to doltlite {version}")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as handle:
            handle.write(f"version={version}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
