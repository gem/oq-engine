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

from numpy.testing import assert_allclose

from openquake.commonlib import readinput, valid
from openquake.baselib import general

TMP = tempfile.gettempdir()


class ParseConfigTestCase(unittest.TestCase):

    def test_get_oqparam_with_files(self):
        temp_dir = tempfile.mkdtemp()
        site_model_input = general.writetmp(dir=temp_dir, content="foo")
        job_config = general.writetmp(dir=temp_dir, content="""
[general]
calculation_mode = classical
[foo]
bar = baz
[site]
sites = 0 0
site_model_file = %s
maximum_distance=1
truncation_level=0
random_seed=0
intensity_measure_types = PGA
investigation_time = 50
export_dir = %s
        """ % (site_model_input, TMP))

        try:
            exp_base_path = os.path.dirname(job_config)

            expected_params = {
                'export_dir': TMP,
                'base_path': exp_base_path,
                'calculation_mode': 'classical',
                'truncation_level': 0.0,
                'random_seed': 0,
                'reference_backarc': False,
                'maximum_distance': 1.0,
                'inputs': {'job_ini': job_config,
                           'site_model': site_model_input},
                'sites': [(0.0, 0.0)],
                'hazard_imtls': {'PGA': None},
                'investigation_time': 50.0,
            }

            with mock.patch('logging.warn') as warn:
                params = vars(readinput.get_oqparam(job_config))
                print params
                print expected_params
                self.assertEqual(expected_params, params)
                self.assertEqual(['site_model', 'job_ini'],
                                 params['inputs'].keys())
                self.assertEqual([site_model_input, job_config],
                                 params['inputs'].values())

                # checking that warnings work
                self.assertEqual(warn.call_args[0][0],
                                 "The parameter 'bar' is unknown, ignoring")
        finally:
            shutil.rmtree(temp_dir)

    def test_get_oqparam_with_sites_csv(self):
        sites_csv = general.writetmp('1.0,2.1\n3.0,4.1\n5.0,6.1')
        try:
            source = general.writetmp("""
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
intensity_measure_types_and_levels = {'PGA': [0.1, 0.2]}
investigation_time = 50.
export_dir = %s
            """ % (sites_csv, TMP))
            exp_base_path = os.path.dirname(
                os.path.join(os.path.abspath('.'), source))

            expected_params = {
                'export_dir': TMP,
                'base_path': exp_base_path,
                'calculation_mode': 'classical',
                'truncation_level': 3.0,
                'random_seed': 5,
                'maximum_distance': 1.0,
                'reference_backarc': False,
                'inputs': {'job_ini': source,
                           'sites': sites_csv},
                'reference_depth_to_1pt0km_per_sec': 100.0,
                'reference_depth_to_2pt5km_per_sec': 5.0,
                'reference_vs30_type': 'measured',
                'reference_vs30_value': 600.0,
                'hazard_imtls': {'PGA': [0.1, 0.2]},
                'investigation_time': 50.0,
            }

            params = vars(readinput.get_oqparam(source))
            self.assertEqual(expected_params, params)
        finally:
            os.unlink(sites_csv)

    def test_wrong_discretization(self):
        source = general.writetmp("""
[general]
calculation_mode = classical
region = 27.685048 85.280857, 27.736719 85.280857, 27.733376 85.355358, 27.675015 85.355358
region_grid_spacing = 5.0
maximum_distance=1
truncation_level=3
random_seed=5
reference_vs30_type = measured
reference_vs30_value = 600.0
reference_depth_to_2pt5km_per_sec = 5.0
reference_depth_to_1pt0km_per_sec = 100.0
intensity_measure_types = PGA
investigation_time = 50.
""")
        oqparam = readinput.get_oqparam(source)
        with self.assertRaises(ValueError) as ctx:
            readinput.get_site_collection(oqparam)
        self.assertIn('Could not discretize region', str(ctx.exception))


class ClosestSiteModelTestCase(unittest.TestCase):

    def test_get_site_model(self):
        data = StringIO('''\
<?xml version="1.0" encoding="utf-8"?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
    <siteModel>
        <site lon="0.0" lat="0.0" vs30="1200.0" vs30Type="inferred" z1pt0="100.0" z2pt5="2.0" backarc="False" />
        <site lon="0.0" lat="0.1" vs30="600.0" vs30Type="inferred" z1pt0="100.0" z2pt5="2.0" backarc="True" />
        <site lon="0.0" lat="0.2" vs30="200.0" vs30Type="inferred" z1pt0="100.0" z2pt5="2.0" backarc="False" />
    </siteModel>
</nrml>''')
        oqparam = mock.Mock()
        oqparam.inputs = dict(site_model=data)
        expected = [
            valid.SiteParam(z1pt0=100.0, z2pt5=2.0, measured=False,
                            vs30=1200.0, backarc=False, lon=0.0, lat=0.0),
            valid.SiteParam(z1pt0=100.0, z2pt5=2.0, measured=False,
                            vs30=600.0, backarc=True, lon=0.0, lat=0.1),
            valid.SiteParam(z1pt0=100.0, z2pt5=2.0, measured=False,
                            vs30=200.0, backarc=False, lon=0.0, lat=0.2)]
        self.assertEqual(list(readinput.get_site_model(oqparam)), expected)


class ExposureTestCase(unittest.TestCase):
    exposure = general.writetmp('''\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4">
  <exposureModel id="ep" category="buildings">
    <description>Exposure model for buildings</description>
    <conversions>
      <costTypes>
        <costType name="structural" unit="USD" type="per_asset"/>
      </costTypes>
    </conversions>
    <assets>
      <asset id="a1" taxonomy="RM" number="3000">
        <location lon="81.2985" lat="29.1098"/>
        <costs>
          <cost type="structural" value="1000"/>
        </costs>
      </asset>
      <asset id="a2" taxonomy="RC">
        <location lon="83.082298" lat="27.9006"/>
        <costs>
          <cost type="structural" value="500"/>
        </costs>
      </asset>
      <asset id="a3" taxonomy="W" number="2000">
        <location lon="85.747703" lat="27.9015"/>
        <costs>
          <cost type="structural" value="1000"/>
        </costs>
      </asset>
    </assets>
  </exposureModel>
</nrml>''')

    def test_get_exposure_metadata(self):
        exp, _assets = readinput.get_exposure_lazy(self.exposure)
        self.assertEqual(exp.description, 'Exposure model for buildings')
        self.assertEqual(exp.insurance_limit_is_absolute, None)
        self.assertEqual(exp.deductible_is_absolute, None)
        self.assertEqual(exp.cost_types, [
            {'type': 'per_asset', 'name': 'structural', 'unit': 'USD'}])

    def test_exposure_missing_number(self):
        oqparam = mock.Mock()
        oqparam.calculation_mode = 'scenario_damage'
        oqparam.inputs = {'exposure': self.exposure}
        oqparam.region_constraint = '''\
POLYGON((78.0 31.5, 89.5 31.5, 89.5 25.5, 78.0 25.5, 78.0 31.5))'''
        oqparam.time_event = None

        with self.assertRaises(KeyError) as ctx:
            readinput.get_exposure(oqparam)
        self.assertIn("node asset: 'number', line 17 of", str(ctx.exception))


class ReadCsvTestCase(unittest.TestCase):
    def test_get_mesh_csvdata_ok(self):
        fakecsv = StringIO("""\
PGA 12.0 42.0 0.14 0.15 0.16
PGA 12.0 42.1 0.44 0.45 0.46
PGA 12.0 42.2 0.64 0.65 0.66
PGV 12.0 42.0 0.24 0.25 0.26
PGV 12.0 42.1 0.34 0.35 0.36
PGV 12.0 42.2 0.54 0.55 0.56
""")
        mesh, data = readinput.get_mesh_csvdata(
            fakecsv, ['PGA', 'PGV'], [3, 3], valid.probabilities)
        assert_allclose(mesh.lons, [12., 12., 12.])
        assert_allclose(mesh.lats, [42., 42.1, 42.2])
        assert_allclose(data['PGA'], [[0.14, 0.15, 0.16],
                                      [0.44, 0.45, 0.46],
                                      [0.64, 0.65, 0.66]])
        assert_allclose(data['PGV'], [[0.24, 0.25, 0.26],
                                      [0.34, 0.35, 0.36],
                                      [0.54, 0.55, 0.56]])

    def test_get_mesh_csvdata_different_levels(self):
        fakecsv = StringIO("""\
PGA 12.0 42.0 0.14 0.15 0.16
PGA 12.0 42.1 0.44 0.45 0.46
PGA 12.0 42.2 0.64 0.65 0.66
PGV 12.0 42.0 0.24 0.25
PGV 12.0 42.1 0.34 0.35
PGV 12.0 42.2 0.54 0.55
""")
        mesh, data = readinput.get_mesh_csvdata(
            fakecsv, ['PGA', 'PGV'], [3, 2], valid.probabilities)
        assert_allclose(mesh.lons, [12., 12., 12.])
        assert_allclose(mesh.lats, [42., 42.1, 42.2])
        assert_allclose(data['PGA'], [[0.14, 0.15, 0.16],
                                      [0.44, 0.45, 0.46],
                                      [0.64, 0.65, 0.66]])
        assert_allclose(data['PGV'], [[0.24, 0.25],
                                      [0.34, 0.35],
                                      [0.54, 0.55]])

    def test_get_mesh_csvdata_err1(self):
        # a negative probability
        fakecsv = StringIO("""\
PGA 12.0 42.0 0.14 0.15 0.16
PGA 12.0 42.1 0.44 0.45 0.46
PGA 12.0 42.2 0.64 0.65 0.66
PGV 12.0 42.0 0.24 0.25 -0.26
PGV 12.0 42.1 0.34 0.35 0.36
PGV 12.0 42.2 0.54 0.55 0.56
""")
        with self.assertRaises(ValueError) as ctx:
            readinput.get_mesh_csvdata(
                fakecsv, ['PGA', 'PGV'], [3, 3], valid.probabilities)
        self.assertIn('line 4', str(ctx.exception))

    def test_get_mesh_csvdata_err2(self):
        # a duplicated point
        fakecsv = StringIO("""\
PGA 12.0 42.0 0.14 0.15 0.16
PGA 12.0 42.1 0.44 0.45 0.46
PGA 12.0 42.2 0.64 0.65 0.66
PGV 12.0 42.1 0.24 0.25 0.26
PGV 12.0 42.1 0.34 0.35 0.36
""")
        with self.assertRaises(readinput.DuplicatedPoint) as ctx:
            readinput.get_mesh_csvdata(
                fakecsv, ['PGA', 'PGV'], [3, 3], valid.probabilities)
        self.assertIn('line 5', str(ctx.exception))

    def test_get_mesh_csvdata_err3(self):
        # a missing location for PGV
        fakecsv = StringIO("""\
PGA 12.0 42.0 0.14 0.15 0.16
PGA 12.0 42.1 0.44 0.45 0.46
PGA 12.0 42.2 0.64 0.65 0.66
PGV 12.0 42.0 0.24 0.25 0.26
PGV 12.0 42.1 0.34 0.35 0.36
""")
        with self.assertRaises(ValueError) as ctx:
            readinput.get_mesh_csvdata(
                fakecsv, ['PGA', 'PGV'], [3, 3], valid.probabilities)
        self.assertEqual(str(ctx.exception),
                         'Inconsistent locations between PGA and PGV')

    def test_get_mesh_csvdata_err4(self):
        # inconsistent number of levels
        fakecsv = StringIO("""\
PGA 12.0 42.0 0.14 0.15
PGA 12.0 42.1 0.44 0.45 0.46
PGA 12.0 42.2 0.64
""")
        with self.assertRaises(ValueError) as ctx:
            readinput.get_mesh_csvdata(
                fakecsv, ['PGA'], [2], valid.probabilities)
        self.assertIn('Found 3 values, expected 2', str(ctx.exception))

    def test_get_mesh_csvdata_err5(self):
        # unexpected IMT
        fakecsv = StringIO("""\
PGA 12.0 42.0 0.14 0.15
PGA 12.0 42.1 0.44 0.45
PGA 12.0 42.2 0.64 0.65
""")
        with self.assertRaises(ValueError) as ctx:
            readinput.get_mesh_csvdata(
                fakecsv, ['PGV'], [3], valid.probabilities)
        self.assertIn("Got 'PGA', expected PGV", str(ctx.exception))
