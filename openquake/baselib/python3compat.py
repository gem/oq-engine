from __future__ import print_function
import os
import sys
import importlib
import subprocess


def check_syntax(pkg):
    """
    Recursively check all modules in the given package for compatibility with
    Python 3 syntax. No imports are performed.

    :param pkg: a Python package
    """
    ok, err = 0, 0
    for cwd, dirs, files in os.walk(pkg.__path__[0]):
        for f in files:
            if f.endswith('.py'):
                fname = os.path.join(cwd, f)
                errno = subprocess.call(['python3', '-m', 'py_compile', fname])
                if errno:
                    err += 1
                else:
                    ok += 1
    print('Checked %d ok, %d wrong modules' % (ok, err))


if __name__ == '__main__':
    check_syntax(importlib.import_module(sys.argv[1]))
