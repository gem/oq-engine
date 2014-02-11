oq-engine-server
================

### Running Tests ###

Here are some examples for how to run tests. Both methods must be run from the
`openquakeserver` directory.

Using Django's manage.py:

    $ python manage.py test --settings=test_db_settings

    Note: You need to install Django South for this to work.

Using nosetests:

    $ (export DJANGO_SETTINGS_MODULE="openquak.eserver.settings"; nosetests -v --with-coverage --cover-package=openquake.server)
