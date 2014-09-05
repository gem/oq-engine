import StringIO
import os
import shutil
import tempfile
import unittest
from openquake.commonlib import readini, general


class ParseConfigTestCase(unittest.TestCase):

    def test_parse_config_no_files(self):
        # sections are there just for documentation
        # when we parse the file, we ignore these
        source = StringIO.StringIO("""
[general]
CALCULATION_MODE = classical_risk
region = 1 1, 2 2, 3 3
[foo]
bar = baz
""")
        # Add a 'name' to make this look like a real file:
        source.name = 'path/to/some/job.ini'
        exp_base_path = os.path.dirname(
            os.path.join(os.path.abspath('.'), source.name))

        expected_params = {
            'base_path': exp_base_path,
            'calculation_mode': 'classical_risk',
            'region': [(1.0, 1.0), (2.0, 2.0), (3.0, 3.0)],
            'inputs': {},
            'sites': None
        }

        params = vars(readini.parse_config(source))

        self.assertEqual(expected_params, params)

    def test_parse_config_with_files(self):
        temp_dir = tempfile.mkdtemp()
        site_model_input = general.writetmp(dir=temp_dir, content="foo")
        job_config = general.writetmp(dir=temp_dir, content="""
[general]
calculation_mode = classical
[site]
sites = 0 0
site_model_file = %s
maximum_distance=0
truncation_level=0
random_seed=0
    """ % site_model_input)

        try:
            exp_base_path = os.path.dirname(job_config)

            expected_params = {
                'base_path': exp_base_path,
                'calculation_mode': 'classical',
                'truncation_level': 0.0,
                'random_seed': 0,
                'maximum_distance': 0.0,
                'inputs': {'site_model': site_model_input},
                'sites': [(0.0, 0.0)],
            }

            params = vars(readini.parse_config(open(job_config)))
            self.assertEqual(expected_params, params)
            self.assertEqual(['site_model'], params['inputs'].keys())
            self.assertEqual([site_model_input], params['inputs'].values())
        finally:
            shutil.rmtree(temp_dir)

    def test_parse_config_with_sites_csv(self):
        sites_csv = general.writetmp(content='1.0,2.1\n3.0,4.1\n5.0,6.1')
        try:
            source = StringIO.StringIO("""
[general]
calculation_mode = classical
[geometry]
sites_csv = %s
[misc]
maximum_distance=0
truncation_level=3
random_seed=5
[site_params]
reference_vs30_type = measured
reference_vs30_value = 600.0
reference_depth_to_2pt5km_per_sec = 5.0
reference_depth_to_1pt0km_per_sec = 100.0
""" % sites_csv)
            source.name = 'path/to/some/job.ini'
            exp_base_path = os.path.dirname(
                os.path.join(os.path.abspath('.'), source.name))

            expected_params = {
                'base_path': exp_base_path,
                'sites': [(1.0, 2.1), (3.0, 4.1), (5.0, 6.1)],
                'calculation_mode': 'classical',
                'truncation_level': 3.0,
                'random_seed': 5,
                'maximum_distance': 0.0,
                'inputs': {},
                'reference_depth_to_1pt0km_per_sec': 100.0,
                'reference_depth_to_2pt5km_per_sec': 5.0,
                'reference_vs30_type': 'measured',
                'reference_vs30_value': 600.0,
            }

            params = vars(readini.parse_config(source))
            self.assertEqual(expected_params, params)
        finally:
            os.unlink(sites_csv)
