#!/usr/bin/env bash
set -e
set -x
quarto render ./**/*.qmd --to=ipynb
find . -name "*.ipynb" -exec sh -c 'pandoc "${0}" -t gfm -o "${0%.ipynb}.md"' {} \;
