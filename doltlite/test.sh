#!/usr/bin/env bash
# Run the recipe tests for every package built into this directory.
# pixi build only packages; the tests declared in recipe.yaml are run here.
set -euo pipefail

shopt -s nullglob
packages=(doltlite-*.conda)
if [ ${#packages[@]} -eq 0 ]; then
    echo "no doltlite-*.conda found; run 'pixi run build <platform>' first" >&2
    exit 1
fi

for package in "${packages[@]}"; do
    echo "==> testing ${package}"
    rattler-build test -p "${package}" -c conda-forge
done
