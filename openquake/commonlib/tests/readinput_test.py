# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
import shutil
import tempfile
import mock
import unittest
import collections
from io import BytesIO, StringIO

from numpy.testing import assert_allclose

from openquake.baselib import general
from openquake.hazardlib import valid
from openquake.risklib.riskinput import ValidationError
from openquake.commonlib import readinput, writers
from openquake.qa_tests_data.classical import case_1, case_2
from openquake.qa_tests_data.event_based_risk import case_caracas


TMP = tempfile.gettempdir()
DATADIR = os.path.join(os.path.dirname(__file__), 'data')


def getparams(oq):
    return {k: v for k, v in vars(oq).items() if not k.startswith('_')}


class ParseConfigTestCase(unittest.TestCase):

    def test_get_oqparam_with_files(self):
        temp_dir = tempfile.mkdtemp()
        site_model_input = general.writetmp(dir=temp_dir, content="foo")
        job_config = general.writetmp(dir=temp_dir, content="""
[general]
calculation_mode = event_based
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
                'calculation_mode': 'event_based',
                'truncation_level': 0.0,
                'random_seed': 0,
                'maximum_distance': {'default': 1},
                'inputs': {'job_ini': job_config,
                           'site_model': site_model_input},
                'sites': [(0.0, 0.0, 0.0)],
                'hazard_imtls': {'PGA': None},
                'investigation_time': 50.0,
                'risk_investigation_time': 50.0,
            }

            with mock.patch('logging.warn') as warn:
                params = getparams(readinput.get_oqparam(job_config))
                for key in expected_params:
                    self.assertEqual(expected_params[key], params[key])
                items = sorted(params['inputs'].items())
                keys, values = zip(*items)
                self.assertEqual(('job_ini', 'site_model'), keys)
                self.assertEqual((job_config, site_model_input), values)

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
                'maximum_distance': {'default': 1},
                'inputs': {'job_ini': source,
                           'sites': sites_csv},
                'reference_depth_to_1pt0km_per_sec': 100.0,
                'reference_depth_to_2pt5km_per_sec': 5.0,
                'reference_vs30_type': 'measured',
                'reference_vs30_value': 600.0,
                'hazard_imtls': {'PGA': [0.1, 0.2]},
                'investigation_time': 50.0,
                'risk_investigation_time': 50.0,
            }

            params = getparams(readinput.get_oqparam(source))
            self.assertEqual(expected_params, params)
        finally:
            os.unlink(sites_csv)

    def test_wrong_discretization(self):
        source = general.writetmp("""
[general]
calculation_mode = event_based
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


def sitemodel():
    return BytesIO(b'''\
<?xml version="1.0" encoding="utf-8"?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
    <siteModel>
        <site lon="0.0" lat="0.0" vs30="1200.0" vs30Type="inferred" z1pt0="100.0" z2pt5="2.0" backarc="False" />
        <site lon="0.0" lat="0.1" vs30="600.0" vs30Type="inferred" z1pt0="100.0" z2pt5="2.0" backarc="True" />
        <site lon="0.0" lat="0.2" vs30="200.0" vs30Type="inferred" z1pt0="100.0" z2pt5="2.0" backarc="False" />
    </siteModel>
</nrml>''')


class ClosestSiteModelTestCase(unittest.TestCase):

    def test_get_site_model(self):
        oqparam = mock.Mock()
        oqparam.base_path = '/'
        oqparam.inputs = dict(site_model=sitemodel())
        expected = [
            valid.SiteParam(z1pt0=100.0, z2pt5=2.0, measured=False,
                            vs30=1200.0, backarc=False, lon=0.0, lat=0.0,
                            depth=0.0),
            valid.SiteParam(z1pt0=100.0, z2pt5=2.0, measured=False,
                            vs30=600.0, backarc=True, lon=0.0, lat=0.1,
                            depth=0.0),
            valid.SiteParam(z1pt0=100.0, z2pt5=2.0, measured=False,
                            vs30=200.0, backarc=False, lon=0.0, lat=0.2,
                            depth=0.0)]
        self.assertEqual(list(readinput.get_site_model(oqparam)), expected)

    def test_get_far_away_parameter(self):
        oqparam = mock.Mock()
        oqparam.base_path = '/'
        oqparam.maximum_distance = 100
        oqparam.max_site_model_distance = 5
        oqparam.sites = [(1.0, 0, 0)]
        oqparam.inputs = dict(site_model=sitemodel())
        with mock.patch('logging.warn') as warn:
            readinput.get_site_collection(oqparam)
        # check that the warning was raised
        self.assertEqual(
            warn.call_args[0][0],
            'The site parameter associated to '
            '<Latitude=0.000000, Longitude=1.000000, Depth=0.0000> '
            'came from a distance of 111 km!')


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

    exposure0 = general.writetmp('''\
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
      <asset id="a2" taxonomy="RC" number="0">
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

    exposure1 = general.writetmp('''\
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
      <asset id="a 1" taxonomy="RM" number="3000">
        <location lon="81.2985" lat="29.1098"/>
        <costs>
          <cost type="structural" value="1000"/>
        </costs>
      </asset>
    </assets>
  </exposureModel>
</nrml>''')

    exposure2 = general.writetmp('''\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">
  <exposureModel id="ep" category="buildings">
    <description>Exposure model for buildings</description>
    <conversions>
      <costTypes>
        <costType name="structural" unit="USD" type="aggregate"/>
      </costTypes>
    </conversions>
  </exposureModel>
</nrml>''')  # wrong cost type "aggregate"

    def test_get_exposure_metadata(self):
        exp, _assets = readinput._get_exposure(
            self.exposure, ['structural'], stop='assets')
        self.assertEqual(exp.description, 'Exposure model for buildings')
        self.assertTrue(exp.insurance_limit_is_absolute)
        self.assertTrue(exp.deductible_is_absolute)
        self.assertEqual([tuple(ct) for ct in exp.cost_types],
                         [('structural', 'per_asset', 'USD')])

    def test_exposure_missing_number(self):
        oqparam = mock.Mock()
        oqparam.base_path = '/'
        oqparam.calculation_mode = 'scenario_damage'
        oqparam.all_cost_types = ['occupants']
        oqparam.inputs = {'exposure': self.exposure}
        oqparam.region_constraint = '''\
POLYGON((78.0 31.5, 89.5 31.5, 89.5 25.5, 78.0 25.5, 78.0 31.5))'''
        oqparam.time_event = None
        oqparam.ignore_missing_costs = []

        with self.assertRaises(KeyError) as ctx:
            readinput.get_exposure(oqparam)
        self.assertIn("node asset: 'number', line 17 of", str(ctx.exception))

    def test_exposure_zero_number(self):
        oqparam = mock.Mock()
        oqparam.base_path = '/'
        oqparam.calculation_mode = 'scenario_damage'
        oqparam.all_cost_types = ['structural']
        oqparam.insured_losses = False
        oqparam.inputs = {'exposure': self.exposure0}
        oqparam.region_constraint = '''\
POLYGON((78.0 31.5, 89.5 31.5, 89.5 25.5, 78.0 25.5, 78.0 31.5))'''
        oqparam.time_event = None
        oqparam.ignore_missing_costs = []

        with self.assertRaises(ValueError) as ctx:
            readinput.get_exposure(oqparam)
        self.assertIn("Could not convert number->compose"
                      "(positivefloat,nonzero): '0' is zero, line 17",
                      str(ctx.exception))

    def test_exposure_invalid_asset_id(self):
        oqparam = mock.Mock()
        oqparam.base_path = '/'
        oqparam.calculation_mode = 'scenario_damage'
        oqparam.all_cost_types = ['structural']
        oqparam.inputs = {'exposure': self.exposure1}
        oqparam.region_constraint = '''\
POLYGON((78.0 31.5, 89.5 31.5, 89.5 25.5, 78.0 25.5, 78.0 31.5))'''
        oqparam.time_event = None
        oqparam.ignore_missing_costs = []
        with self.assertRaises(ValueError) as ctx:
            readinput.get_exposure(oqparam)
        self.assertIn("Invalid ID 'a 1': the only accepted chars are "
                      "a-zA-Z0-9_-, line 11", str(ctx.exception))

    def test_exposure_no_insured_data(self):
        oqparam = mock.Mock()
        oqparam.base_path = '/'
        oqparam.calculation_mode = 'scenario_risk'
        oqparam.all_cost_types = ['structural']
        oqparam.insured_losses = True
        oqparam.inputs = {'exposure': self.exposure,
                          'structural_vulnerability': None}
        oqparam.region_constraint = '''\
POLYGON((78.0 31.5, 89.5 31.5, 89.5 25.5, 78.0 25.5, 78.0 31.5))'''
        oqparam.time_event = None
        oqparam.ignore_missing_costs = []
        with self.assertRaises(KeyError) as ctx:
            readinput.get_exposure(oqparam)
        self.assertIn("node cost: 'deductible', line 14", str(ctx.exception))

    def test_exposure_no_assets(self):
        oqparam = mock.Mock()
        oqparam.base_path = '/'
        oqparam.calculation_mode = 'scenario_risk'
        oqparam.all_cost_types = ['structural']
        oqparam.insured_losses = True
        oqparam.inputs = {'exposure': self.exposure,
                          'structural_vulnerability': None}
        oqparam.region_constraint = '''\
POLYGON((68.0 31.5, 69.5 31.5, 69.5 25.5, 68.0 25.5, 68.0 31.5))'''
        oqparam.time_event = None
        oqparam.ignore_missing_costs = []
        with self.assertRaises(RuntimeError) as ctx:
            readinput.get_exposure(oqparam)
        self.assertIn('Could not find any asset within the region!',
                      str(ctx.exception))

    def test_exposure_wrong_cost_type(self):
        oqparam = mock.Mock()
        oqparam.base_path = '/'
        oqparam.calculation_mode = 'scenario_risk'
        oqparam.all_cost_types = ['structural']
        oqparam.region_constraint = '''\
POLYGON((68.0 31.5, 69.5 31.5, 69.5 25.5, 68.0 25.5, 68.0 31.5))'''
        oqparam.inputs = {'exposure': self.exposure2,
                          'structural_vulnerability': None}
        with self.assertRaises(ValueError) as ctx:
            readinput.get_exposure(oqparam)
        self.assertIn("Got 'aggregate', expected "
                      "aggregated|per_area|per_asset, line 7",
                      str(ctx.exception))


class ReadCsvTestCase(unittest.TestCase):
    def test_get_mesh_csvdata_ok(self):
        fakecsv = StringIO(u"""\
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
        fakecsv = StringIO(u"""\
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
        fakecsv = StringIO(u"""\
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
        fakecsv = StringIO(u"""\
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
        fakecsv = StringIO(u"""\
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
        fakecsv = StringIO(u"""\
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
        fakecsv = StringIO(u"""\
PGA 12.0 42.0 0.14 0.15
PGA 12.0 42.1 0.44 0.45
PGA 12.0 42.2 0.64 0.65
""")
        with self.assertRaises(ValueError) as ctx:
            readinput.get_mesh_csvdata(
                fakecsv, ['PGV'], [3], valid.probabilities)
        self.assertIn("Got 'PGA', expected PGV", str(ctx.exception))

    def test_get_mesh_hcurves_ok(self):
        fakecsv = StringIO(u"""\
0 0, 0.42 0.24 0.14, 0.25 0.16 0.08
0 1, 0.42 0.24 0.14, 0.45 0.40 0.18
0 2, 0.42 0.24 0.14, 0.65 0.64 0.60
0 3, 0.42 0.24 0.14, 0.25 0.21 0.20
0 4, 0.42 0.24 0.04, 0.35 0.31 0.30
0 5, 0.42 0.24 0.04, 0.55 0.51 0.50
""")
        oqparam = mock.Mock()
        oqparam.base_path = '/'
        oqparam.inputs = dict(hazard_curves=fakecsv)
        oqparam.imtls = collections.OrderedDict([
            ('PGA', [0.1, 0.2, 0.3]),
            ('PGV', [0.11, 0.22, 0.33])])
        mesh, data = readinput.get_mesh_hcurves(oqparam)
        assert_allclose(mesh.lons, [0., 0., 0., 0., 0., 0.])
        assert_allclose(mesh.lats, [0., 1., 2., 3., 4., 5.])
        assert_allclose(data['PGA'], [[0.42, 0.24, 0.14],
                                      [0.42, 0.24, 0.14],
                                      [0.42, 0.24, 0.14],
                                      [0.42, 0.24, 0.14],
                                      [0.42, 0.24, 0.04],
                                      [0.42, 0.24, 0.04]])
        assert_allclose(data['PGV'], [[0.25, 0.16, 0.08],
                                      [0.45, 0.4, 0.18],
                                      [0.65, 0.64, 0.6],
                                      [0.25, 0.21, 0.2],
                                      [0.35, 0.31, 0.3],
                                      [0.55, 0.51, 0.5]])


class TestReadGmfCsvTestCase(unittest.TestCase):
    def setUp(self):
        self.oqparam = mock.Mock()
        self.oqparam.base_path = '/'
        self.oqparam.inputs = {}
        self.oqparam.imtls = {'PGA': None}
        self.oqparam.number_of_ground_motion_fields = 3

    def test_gmf_ok(self):
        fname = general.writetmp('''\
0 0,0 1
col=00|ses=0001|src=test|rup=001-00,0 1,3.05128000E-01 6.04032000E-01
col=00|ses=0001|src=test|rup=001-01,0 1,2.67031000E-01 3.34878000E-01
col=00|ses=0001|src=test|rup=001-02,0 1,1.59434000E-01 3.92602000E-01
''')
        _, _, gmfs = readinput.get_gmfs_from_txt(self.oqparam, fname)
        gmvs1, gmvs2 = gmfs['PGA']
        assert_allclose(gmvs1, [0.305128, 0.267031, 0.159434])
        assert_allclose(gmvs2, [0.604032, 0.334878, 0.392602])

    def test_missing_indices_are_ok(self):
        fname = general.writetmp('''\
0 0,0 1
col=00|ses=0001|src=test|rup=001-00,,1.59434000E-01 3.92602000E-01
col=00|ses=0001|src=test|rup=001-01,0 1,3.05128000E-01 6.04032000E-01
col=00|ses=0001|src=test|rup=001-02,0,2.67031000E-01
''')
        _, _, gmfs = readinput.get_gmfs_from_txt(self.oqparam, fname)
        gmvs1, gmvs2 = gmfs['PGA']
        assert_allclose(gmvs1, [0.159434, 0.305128, 0.267031])
        assert_allclose(gmvs2, [0.392602, 0.604032, 0.])

    def test_negative_gmf(self):
        fname = general.writetmp('''\
0 0,0 1
col=00|ses=0001|src=test|rup=001-00,0 1,3.05128000E-01 6.04032000E-01
col=00|ses=0001|src=test|rup=001-01,0 1,2.67031000E-01 3.34878000E-01
col=00|ses=0001|src=test|rup=001-02,0 1,1.59434000E-01 -3.92602000E-01
''')
        with self.assertRaises(readinput.InvalidFile):
            readinput.get_gmfs_from_txt(self.oqparam, fname)

    def test_missing_line(self):
        fname = general.writetmp('''\
0 0,0 1
col=00|ses=0001|src=test|rup=001-00,0 1,3.05128000E-01 6.04032000E-01
col=00|ses=0001|src=test|rup=001-01,0 1,2.67031000E-01 3.34878000E-01
''')
        with self.assertRaises(readinput.InvalidFile):
            readinput.get_gmfs_from_txt(self.oqparam, fname)

    def test_not_ordered_etags(self):
        fname = general.writetmp('''\
0 0,0 1
col=00|ses=0001|src=test|rup=001-02,0 1,1.59434000E-01 3.92602000E-01
col=00|ses=0001|src=test|rup=001-00,0 1,3.05128000E-01 6.04032000E-01
col=00|ses=0001|src=test|rup=001-01,0 1,2.67031000E-01 3.34878000E-01
''')
        with self.assertRaises(readinput.InvalidFile):
            readinput.get_gmfs_from_txt(self.oqparam, fname)

    def test_negative_indices(self):
        fname = general.writetmp('''\
0 0,0 1
col=00|ses=0001|src=test|rup=001-00,0 -1,1.59434000E-01 3.92602000E-01
col=00|ses=0001|src=test|rup=001-01,0 1,3.05128000E-01 6.04032000E-01
col=00|ses=0001|src=test|rup=001-02,0 1,2.67031000E-01 3.34878000E-01
''')
        with self.assertRaises(readinput.InvalidFile):
            readinput.get_gmfs_from_txt(self.oqparam, fname)

    def test_missing_bad_indices(self):
        fname = general.writetmp('''\
0 0,0 1
col=00|ses=0001|src=test|rup=001-00,,1.59434000E-01 3.92602000E-01
col=00|ses=0001|src=test|rup=001-01,0 1,3.05128000E-01 6.04032000E-01
col=00|ses=0001|src=test|rup=001-02,X,2.67031000E-01
''')
        with self.assertRaises(readinput.InvalidFile):
            readinput.get_gmfs_from_txt(self.oqparam, fname)


class TestReadGmfXmlTestCase(unittest.TestCase):
    """
    Read the GMF from a NRML file
    """
    def setUp(self):
        self.oqparam = mock.Mock()
        self.oqparam.base_path = '/'
        self.oqparam.inputs = {}
        self.oqparam.imtls = {'PGA': None, 'PGV': None}
        self.oqparam.number_of_ground_motion_fields = 5

    def test_ok(self):
        fname = os.path.join(DATADIR,  'gmfdata.xml')
        sitecol, etags, gmfa = readinput.get_scenario_from_nrml(
            self.oqparam, fname)
        coords = list(zip(sitecol.mesh.lons, sitecol.mesh.lats))
        self.assertEqual(writers.write_csv(StringIO(), coords), '''\
0.000000E+00,0.000000E+00
0.000000E+00,1.000000E-01
0.000000E+00,2.000000E-01''')
        assert_allclose(etags, range(5))
        self.assertEqual(
            writers.write_csv(StringIO(), gmfa), '''\
PGA:float32,PGV:float32
6.824957E-01 3.656627E-01 8.700833E-01 3.279292E-01 6.968687E-01,6.824957E-01 3.656627E-01 8.700833E-01 3.279292E-01 6.968687E-01
1.270898E-01 2.561812E-01 2.106384E-01 2.357551E-01 2.581405E-01,1.270898E-01 2.561812E-01 2.106384E-01 2.357551E-01 2.581405E-01
1.603097E-01 1.106853E-01 2.232175E-01 1.781143E-01 1.351649E-01,1.603097E-01 1.106853E-01 2.232175E-01 1.781143E-01 1.351649E-01''')

    def test_err(self):
        # missing ruptureId
        fname = os.path.join(DATADIR,  'gmfdata_err.xml')
        with self.assertRaises(readinput.InvalidFile) as ctx:
            readinput.get_scenario_from_nrml(self.oqparam, fname)
        self.assertIn("Found a missing etag '0000000001'",
                      str(ctx.exception))

    def test_err2(self):
        # wrong mesh
        fname = os.path.join(DATADIR,  'gmfdata_err2.xml')
        with self.assertRaises(readinput.InvalidFile) as ctx:
            readinput.get_scenario_from_nrml(self.oqparam, fname)
        self.assertIn("Expected 4 sites, got 3 nodes in", str(ctx.exception))

    def test_tricky_ordering(self):
        # see https://github.com/gem/oq-risklib/issues/546
        fname = general.writetmp('''\
<?xml version="1.0" encoding="utf-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"
      xmlns:gml="http://www.opengis.net/gml">
<gmfCollection gsimTreePath="" sourceModelTreePath="">
  <gmfSet stochasticEventSetId="1">
    <gmf IMT="PGA" ruptureId="0">
      <node gmv="0.0124783118478" lon="12.1244171" lat="43.58248037"/>
      <node gmv="0.0126515007046" lon="12.12477995" lat="43.58217888"/>
      <node gmv="0.0124056290492" lon="12.12478193" lat="43.58120146"/>
    </gmf>
  </gmfSet>
</gmfCollection>
</nrml>''')
        self.oqparam.imtls = {'PGA': None}
        sitecol, _, _ = readinput.get_scenario_from_nrml(self.oqparam, fname)
        self.assertEqual(list(zip(sitecol.lons, sitecol.lats)),
                         [(12.12442, 43.58248),
                          (12.12478, 43.5812),
                          (12.12478, 43.58218)])
        # notice that the last two lats 43.5812, 43.58218 are inverted with
        # respect to the original ordering, 43.58217888, 43.58120146

    def test_two_nodes_on_the_same_point(self):
        # after rounding of the coordinates two points can collide
        fname = general.writetmp('''\
<?xml version="1.0" encoding="utf-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"
      xmlns:gml="http://www.opengis.net/gml">
<gmfCollection gsimTreePath="" sourceModelTreePath="">
  <gmfSet stochasticEventSetId="1">
    <gmf IMT="PGA" ruptureId="0">
      <node gmv="0.0126515007046" lon="12.12477995" lat="43.5812"/>
      <node gmv="0.0124056290492" lon="12.12478193" lat="43.5812"/>
    </gmf>
  </gmfSet>
</gmfCollection>
</nrml>''')
        self.oqparam.imtls = {'PGA': None}
        with self.assertRaises(readinput.InvalidFile) as ctx:
            readinput.get_scenario_from_nrml(self.oqparam, fname)
        self.assertIn("Expected 1 sites, got 2 nodes in", str(ctx.exception))


class TestLoadCurvesTestCase(unittest.TestCase):
    """
    Read the hazard curves from a NRML file
    """
    def test(self):
        fname = general.writetmp('''\
<?xml version="1.0" encoding="utf-8"?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">

    <!-- Spectral Acceleration (SA) example -->
    <hazardCurves sourceModelTreePath="b1_b2_b4" gsimTreePath="b1_b2" investigationTime="50.0" IMT="SA" saPeriod="0.025" saDamping="5.0">
        <IMLs>5.0000e-03 7.0000e-03 1.3700e-02</IMLs>

        <hazardCurve>
            <gml:Point>
                <gml:pos>-122.5000 37.5000</gml:pos>
            </gml:Point>
            <poEs>9.8728e-01 9.8266e-01 9.4957e-01</poEs>
        </hazardCurve>
        <hazardCurve>
            <gml:Point>
                <gml:pos>-123.5000 37.5000</gml:pos>
            </gml:Point>
            <poEs>9.8727e-02 9.8265e-02 9.4956e-02</poEs>
        </hazardCurve>
    </hazardCurves>

    <!-- Basic example, using PGA as IMT -->
    <hazardCurves sourceModelTreePath="b1_b2_b3" gsimTreePath="b1_b7" investigationTime="50.0" IMT="PGA">
        <IMLs>5.0000e-03 7.0000e-03 1.3700e-02 3.3700e-02</IMLs>

        <hazardCurve>
            <gml:Point>
                <gml:pos>-122.5000 37.5000</gml:pos>
            </gml:Point>
            <poEs>9.8728e-01 9.8226e-01 9.4947e-01 9.2947e-01</poEs>
        </hazardCurve>
        <hazardCurve>
            <gml:Point>
                <gml:pos>-123.5000 37.5000</gml:pos>
            </gml:Point>
            <poEs>9.8728e-02 9.8216e-02 9.4945e-02 9.2947e-02</poEs>
        </hazardCurve>
    </hazardCurves>
</nrml>
''', suffix='.xml')
        oqparam = mock.Mock()
        oqparam.inputs = dict(hazard_curves=fname)
        sitecol, hcurves = readinput.get_hcurves(oqparam)
        self.assertEqual(len(sitecol), 2)
        self.assertEqual(sorted(oqparam.hazard_imtls.items()),
                         [('PGA', [0.005, 0.007, 0.0137, 0.0337]),
                          ('SA(0.025)', [0.005, 0.007, 0.0137])])
        self.assertEqual(str(hcurves), '''\
[([0.098727, 0.098265, 0.094956], [0.098728, 0.098216, 0.094945, 0.092947])
 ([0.98728, 0.98266, 0.94957], [0.98728, 0.98226, 0.94947, 0.92947])]''')


class GetCompositeSourceModelTestCase(unittest.TestCase):
    # test the case in_memory=False, used when running `oq info job.ini`

    def test_nrml05(self):
        oq = readinput.get_oqparam('job.ini', case_1)
        csm = readinput.get_composite_source_model(oq, in_memory=False)
        srcs = csm.get_sources()  # a single PointSource
        self.assertEqual(len(srcs), 1)

    def test_nrml04(self):
        oq = readinput.get_oqparam('job.ini', case_2)
        csm = readinput.get_composite_source_model(oq, in_memory=False)
        srcs = csm.get_sources()  # a single PointSource
        self.assertEqual(len(srcs), 1)


class GetCompositeRiskModelTestCase(unittest.TestCase):
    def test_missing_vulnerability_function(self):
        oq = readinput.get_oqparam('job.ini', case_caracas)
        with self.assertRaises(ValidationError):
            readinput.get_risk_model(oq)
