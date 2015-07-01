from __future__ import print_function
import os
import sys
import importlib
import subprocess

PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2

if PY3:
    range = range

    def raise_(tp, value=None, tb=None):
        """
        A function that matches the Python 2.x ``raise`` statement. This
        allows re-raising exceptions with the cls value and traceback on
        Python 2 and 3.
        """
        if value is not None and isinstance(tp, Exception):
            raise TypeError("instance exception may not have a separate value")
        if value is not None:
            exc = tp(value)
        else:
            exc = tp
        if exc.__traceback__ is not tb:
            raise exc.with_traceback(tb)
        raise exc

else:
    range = xrange
   
    exec('''
def raise_(tp, value=None, tb=None):
    raise tp, value, tb
''')


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
