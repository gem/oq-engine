import unittest


class EngineAPITestCase(unittest.TestCase):

    def test_import_job_profile(self):
        """Given a path to a demo config file, ensure that the appropriate
        database records for OqJobProfile, InputSet, and Input are created.
        """
