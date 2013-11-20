# OpenQuake Engine #

OpenQuake is an open source application that allows users to
compute seismic hazard and seismic risk of earthquakes on a global scale.

Please note: the /usr/bin/openquake script requires a celeryconfig.py
file in the PYTHONPATH.  Please make sure this is the case and that your
celeryconfig.py file works with your python-celery setup.

Feel free to copy /usr/openquake/engine/celeryconfig.py and revise it as needed.

## Running tests ##

### Short-running test suite ###
These tests should complete in about 5 minutes:
```bash
$ nosetests --with-doctest tests/
```

### Shorter-running test suite ###
  These tests should complete in about 1 minute:
```bash
$ nosetests --with-doctest -a '!slow' tests/
```

### Full test suite ###
  These tests including many long-running QA tests and can take ~1 hour to run:
```bash
$ nosetests --with-doctest
```

[![githalytics.com alpha](https://cruel-carlota.pagodabox.com/ed9166f60bd7a26c93f0bb34dca7f69b "githalytics.com")](http://githalytics.com/gem/oq-engine)
