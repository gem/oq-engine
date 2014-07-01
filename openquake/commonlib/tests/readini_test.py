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
CALCULATION_MODE = classical
region = 1 1 2 2 3 3
[foo]
bar = baz
""")
        # Add a 'name' to make this look like a real file:
        source.name = 'path/to/some/job.ini'
        exp_base_path = os.path.dirname(
            os.path.join(os.path.abspath('.'), source.name))

        expected_params = {
            'base_path': exp_base_path,
            'calculation_mode': 'classical',
            'region': '1 1 2 2 3 3',
            'bar': 'baz',
            'inputs': {},
        }

        params = readini.parse_config(source)

        self.assertEqual(expected_params, params)

    def test_parse_config_with_files(self):
        temp_dir = tempfile.mkdtemp()
        site_model_input = general.writetmp(dir=temp_dir, content="foo")
        job_config = general.writetmp(dir=temp_dir, content="""
[general]
calculation_mode = classical
[site]
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
                'truncation_level': '0',
                'random_seed': '0',
                'maximum_distance': '0',
                'inputs': {'site_model': site_model_input},
            }

            params = readini.parse_config(open(job_config, 'r'))
            self.assertEqual(expected_params, params)
            self.assertEqual(['site_model'], params['inputs'].keys())
            self.assertEqual([site_model_input], params['inputs'].values())
        finally:
            shutil.rmtree(temp_dir)

    def test__parse_sites_csv(self):
        expected_wkt = 'MULTIPOINT(0.1 0.2, 2 3, 4.1 5.6)'
        source = StringIO.StringIO("""\
0.1,0.2
2,3
4.1,5.6
""")
        wkt = readini._parse_sites_csv(source)
        self.assertEqual(expected_wkt, wkt)

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
""" % sites_csv)
            source.name = 'path/to/some/job.ini'
            exp_base_path = os.path.dirname(
                os.path.join(os.path.abspath('.'), source.name))

            expected_params = {
                'base_path': exp_base_path,
                'sites': 'MULTIPOINT(1.0 2.1, 3.0 4.1, 5.0 6.1)',
                'calculation_mode': 'classical',
                'truncation_level': '3',
                'random_seed': '5',
                'maximum_distance': '0',
                'inputs': {},
            }

            params = readini.parse_config(source)
            self.assertEqual(expected_params, params)
        finally:
            os.unlink(sites_csv)
