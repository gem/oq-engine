#!/bin/bash
cd openquake/server
python manage.py test --settings=test_db_settings
(export DJANGO_SETTINGS_MODULE="openquake.server.settings"; nosetests -v --with-coverage --cover-package=openquake.server)
cd -
