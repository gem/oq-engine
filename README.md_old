OpenQuake Engine
================

OpenQuake is an open source application that allows users to
compute seismic hazard and seismic risk of earthquakes on a global scale.

Please note: the `/usr/bin/oq-engine` script requires a `celeryconfig.py`
file in the `PYTHONPATH`.  Please make sure this is the case and that your
celeryconfig.py file works with your python-celery setup.

Feel free to copy `/usr/openquake/engine/celeryconfig.py` and revise it as needed.

### Running Tests ###

#### Short-running test suite ####

These tests should complete in about 5 minutes:

    $ nosetests --with-doctest tests/

#### Shorter-running test suite ####

These tests should complete in about 1 minute:

    $ nosetests --with-doctest -a '!slow' tests/

#### Full test suite ####

These tests including many long-running QA tests and can take ~1 hour to run:

    $ nosetests --with-doctest


OpenQuake Engine Server
=======================

### Running Tests ###

Here are some examples for how to run tests. Both methods must be run from the
`openquake/server/` directory.

Using Django's manage.py:

    $ python manage.py test --settings=test_db_settings

    Note: You need to install Django South for this to work.

Using nosetests:

    $ (export DJANGO_SETTINGS_MODULE="openquake.server.settings"; nosetests -v --with-coverage --cover-package=openquake.server)

