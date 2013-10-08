#!/bin/bash
cd openquakeserver
python manage.py test --settings=test_db_settings
(export DJANGO_SETTINGS_MODULE="openquakeserver.settings"; nosetests -v --with-coverage --cover-package=openquakeserver)
cd -
