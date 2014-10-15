#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import shutil
import tempfile
import mock
import unittest
from StringIO import StringIO

from openquake.commonlib.readinput import get_site_model, get_oqparam
from openquake.commonlib.valid import SiteParam
from openquake.commonlib import general


class ParseConfigTestCase(unittest.TestCase):

    def test_get_oqparam_no_files(self):
        # sections are there just for documentation
        # when we parse the file, we ignore these
        source = StringIO("""
[general]
CALCULATION_MODE = classical_risk
region = 1 1, 2 2, 3 3
[foo]
bar = baz
intensity_measure_types = PGA
""")
        # Add a 'name' to make this look like a real file:
        source.name = 'path/to/some/job.ini'
        exp_base_path = os.path.dirname(
            os.path.join(os.path.abspath('.'), source.name))

        expected_params = {
            'base_path': exp_base_path,
            'calculation_mode': 'classical_risk',
            'hazard_calculation_id': None,
            'hazard_output_id': 42,
            'region': [(1.0, 1.0), (2.0, 2.0), (3.0, 3.0)],
            'inputs': {},
            'intensity_measure_types_and_levels': {'PGA': None},
        }

        params = vars(get_oqparam(source, hazard_output_id=42))

        self.assertEqual(expected_params, params)

    def test_get_oqparam_with_files(self):
        temp_dir = tempfile.mkdtemp()
        site_model_input = general.writetmp(dir=temp_dir, content="foo")
        job_config = general.writetmp(dir=temp_dir, content="""
[general]
calculation_mode = classical
[site]
sites = 0 0
site_model_file = %s
maximum_distance=1
truncation_level=0
random_seed=0
intensity_measure_types = PGA
    """ % site_model_input)

        try:
            exp_base_path = os.path.dirname(job_config)

            expected_params = {
                'base_path': exp_base_path,
                'calculation_mode': 'classical',
                'hazard_calculation_id': None,
                'hazard_output_id': None,
                'truncation_level': 0.0,
                'random_seed': 0,
                'maximum_distance': 1.0,
                'inputs': {'site_model': site_model_input},
                'sites': [(0.0, 0.0)],
                'intensity_measure_types_and_levels': {'PGA': None},
            }

            params = vars(get_oqparam(open(job_config)))
            self.assertEqual(expected_params, params)
            self.assertEqual(['site_model'], params['inputs'].keys())
            self.assertEqual([site_model_input], params['inputs'].values())
        finally:
            shutil.rmtree(temp_dir)

    def test_get_oqparam_with_sites_csv(self):
        sites_csv = general.writetmp(content='1.0,2.1\n3.0,4.1\n5.0,6.1')
        try:
            source = StringIO("""
[general]
calculation_mode = classical
[geometry]
sites_csv = %s
[misc]
maximum_distance=1
truncation_level=3
random_seed=5
[site_params]
reference_vs30_type = measured
reference_vs30_value = 600.0
reference_depth_to_2pt5km_per_sec = 5.0
reference_depth_to_1pt0km_per_sec = 100.0
intensity_measure_types = PGA
""" % sites_csv)
            source.name = 'path/to/some/job.ini'
            exp_base_path = os.path.dirname(
                os.path.join(os.path.abspath('.'), source.name))

            expected_params = {
                'base_path': exp_base_path,
                'calculation_mode': 'classical',
                'hazard_calculation_id': None,
                'hazard_output_id': None,
                'truncation_level': 3.0,
                'random_seed': 5,
                'maximum_distance': 1.0,
                'inputs': {'sites': sites_csv},
                'reference_depth_to_1pt0km_per_sec': 100.0,
                'reference_depth_to_2pt5km_per_sec': 5.0,
                'reference_vs30_type': 'measured',
                'reference_vs30_value': 600.0,
                'intensity_measure_types_and_levels': {'PGA': None},
            }

            params = vars(get_oqparam(source))
            self.assertEqual(expected_params, params)
        finally:
            os.unlink(sites_csv)


class ClosestSiteModelTestCase(unittest.TestCase):

    def test_get_site_model(self):
        data = StringIO('''\
<?xml version="1.0" encoding="utf-8"?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
    <siteModel>
        <site lon="0.0" lat="0.0" vs30="1200.0" vs30Type="inferred" z1pt0="100.0" z2pt5="2.0" />
        <site lon="0.0" lat="0.1" vs30="600.0" vs30Type="inferred" z1pt0="100.0" z2pt5="2.0" />
        <site lon="0.0" lat="0.2" vs30="200.0" vs30Type="inferred" z1pt0="100.0" z2pt5="2.0" />
    </siteModel>
</nrml>''')
        oqparam = mock.Mock()
        oqparam.inputs = dict(site_model=data)
        expected = [
            SiteParam(z1pt0=100.0, z2pt5=2.0, measured=False, vs30=1200.0,
                      lon=0.0, lat=0.0),
            SiteParam(z1pt0=100.0, z2pt5=2.0, measured=False, vs30=600.0,
                      lon=0.0, lat=0.1),
            SiteParam(z1pt0=100.0, z2pt5=2.0, measured=False, vs30=200.0,
                      lon=0.0, lat=0.2)]
        self.assertEqual(list(get_site_model(oqparam)), expected)
