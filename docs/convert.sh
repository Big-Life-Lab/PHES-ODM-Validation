#!/usr/bin/env bash
set -e
# set -x
script_dir=$(dirname $0)
files="$script_dir/**/*.qmd"
count=$(ls $files | wc -l)
echo "converting $count qmd files to gfm"
echo "rendering..."
quarto render $files --no-cache
echo "converting..."
find . -name "*.html" -exec sh -c 'pandoc "${0}" -t gfm -o "${0%.html}.md"' {} \;
echo "done"
