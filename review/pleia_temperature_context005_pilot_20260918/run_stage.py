"""Path-independent launcher for the temperature delivery stages.

The durable coordinator runs every phase with cwd set to
``smart_building_conformal``, so ``import common`` would otherwise miss this
review directory. This launcher puts the review directory on sys.path itself
and then runs the requested script as __main__, regardless of cwd.
"""
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    if len(sys.argv) < 2:
        raise SystemExit('usage: run_stage.py <script.py> [args...]')
    target = HERE / sys.argv[1]
    if not target.is_file():
        raise SystemExit('no such stage script: ' + str(target))
    sys.path.insert(0, str(HERE))
    sys.argv = [str(target)] + sys.argv[2:]
    runpy.run_path(str(target), run_name='__main__')


if __name__ == '__main__':
    main()
