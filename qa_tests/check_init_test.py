import os

CDIR = os.path.abspath(os.path.dirname(__file__))


def test_init():
    # make sure all QA test directories have an __init__.py file,
    # otherwise nose will not run the tests they contain
    for cwd, dirs, files in os.walk(CDIR):
        for cdir in dirs:
            if cdir.startswith('case_'):
                fname = os.path.join(cwd, cdir, '__init__.py')
                if not os.path.exists(fname):
                    raise IOError('Missing file %s' % fname)
