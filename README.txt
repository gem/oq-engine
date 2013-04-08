OpenQuake is an open source application that allows users to
compute seismic hazard and seismic risk of earthquakes on a global scale.

Please note: the /usr/bin/openquake script requires a celeryconfig.py
file in the PYTHONPATH.  Please make sure this is the case and that your
celeryconfig.py file works with your python-celery setup.

Feel free to copy /usr/openquake/engine/celeryconfig.py and revise it as needed.

**Running tests**

*Short-running test suite*
  These tests should complete in about 5 minutes:
  $ ./run_tests --with-doctest -a '!qa'

*Shorter-running test suite*
  These tests should complete in about 1 minute:
  $ ./run_tests --with-doctest -a '!qa,!slow'

*Full test suite*
  These tests including many long-running QA tests and can take ~1 hour to run:
  $ ./run_tests --with-doctest

Additional `nosetests` arguments can be supplied with these commands.
See https://nose.readthedocs.org/en/latest/usage.html#options.
