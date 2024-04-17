#!/usr/bin/env bash

# Remove backup files and Python cache files
find . -type f \( -name "*.py-e" \
    -o -name "*.DS_Store" \
    -o -name "*.py[co]" \) -delete

# remove coveryage reports
find . -type f \( -name ".coverage*" \
    -o -name ".pytest_*.xml" \) -delete
# Remove cache directories
find . -type d \( -name "__pycache__" \
    -o -name ".mypy_cache" \
    -o -name "htmlcov" \
    -o -name ".ipynb_checkpoints" \
    -o -name ".ruff_cache" \) -execdir rm -rf {} +

# Remove build artifacts, pytest cache, and benchmarks
rm -rf build/ dist/ ./*.egg-info/ .pytest_cache/ .benchmarks/
