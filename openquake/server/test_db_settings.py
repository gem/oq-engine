from django.test.simple import DjangoTestSuiteRunner
from openquake.server.settings import *


DATABASES = {'default': DATABASES['default']}


class NoDbTestRunner(DjangoTestSuiteRunner):
    """ A test runner to test without database creation """

    def setup_databases(self, **kwargs):
        """ Override the database creation defined in parent class """
        pass

    def teardown_databases(self, old_config, **kwargs):
        """ Override the database teardown defined in parent class """
        pass


TEST_RUNNER = "openquake.server.test_db_settings.NoDbTestRunner"
