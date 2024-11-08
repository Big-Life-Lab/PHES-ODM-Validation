#!/usr/bin/env python3
"""Updates quarto documentation
Iterates through each quarto file in the docs folder, converting it to a
markdown document so it can be used by Sphinx.
"""

import os
from pathlib import Path

tool_dir = Path(__file__).parent
root_dir = tool_dir.parent.parent.parent
glob_expr = 'docs/**/*.qmd'

print(f'rendering {glob_expr}')
for path in root_dir.glob(glob_expr):
    cmd = f'quarto render {path} --to gfm'
    print(cmd)
    if os.system(cmd) != 0:
        quit(1)
print('done')
