# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
import tempfile
import unittest.mock as mock
import unittest
from io import BytesIO

from openquake.baselib import general, performance, datastore
from openquake.hazardlib import InvalidFile
from openquake.risklib import asset
from openquake.risklib.riskinput import ValidationError
from openquake.commonlib import readinput
from openquake.qa_tests_data.classical import case_1, case_2, case_21
from openquake.qa_tests_data.event_based import case_16
from openquake.qa_tests_data.event_based_risk import case_caracas


TMP = tempfile.gettempdir()
DATADIR = os.path.join(os.path.dirname(__file__), 'data')


def getparams(oq):
    return {k: v for k, v in vars(oq).items() if not k.startswith('_')}


class ParseConfigTestCase(unittest.TestCase):

    def test_no_absolute_path(self):
        temp_dir = tempfile.mkdtemp()
        site_model_input = general.gettemp(dir=temp_dir, content="foo")
        job_config = general.gettemp(dir=temp_dir, content="""
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
        with self.assertRaises(ValueError) as ctx:
            readinput.get_params([job_config])
        self.assertIn('is an absolute path', str(ctx.exception))

    def test_get_oqparam_with_sites_csv(self):
        sites_csv = general.gettemp('1.0,2.1\n3.0,4.1\n5.0,6.1')
        try:
            source = general.gettemp("""
[general]
calculation_mode = scenario
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
            """ % (os.path.basename(sites_csv), TMP))
            exp_base_path = os.path.dirname(
                os.path.join(os.path.abspath('.'), source))

            expected_params = {
                'export_dir': TMP,
                'base_path': exp_base_path,
                'calculation_mode': 'scenario',
                'truncation_level': 3.0,
                'random_seed': 5,
                'maximum_distance': {'default': 1.0},
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

    def test_wrong_sites_csv(self):
        sites_csv = general.gettemp(
            'site_id,lon,lat\n1,1.0,2.1\n2,3.0,4.1\n3,5.0,6.1')
        source = general.gettemp("""
[general]
calculation_mode = scenario
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
""" % (os.path.basename(sites_csv), TMP))
        oq = readinput.get_oqparam(source)
        with self.assertRaises(InvalidFile) as ctx:
            readinput.get_mesh(oq)
        self.assertIn('expected site_id=0, got 1', str(ctx.exception))
        os.unlink(sites_csv)

    def test_invalid_magnitude_distance_filter(self):
        source = general.gettemp("""
[general]
maximum_distance=[(200, 8)]
""")
        with self.assertRaises(ValueError) as ctx:
            readinput.get_oqparam(source)
        self.assertIn('magnitude 200.0 is bigger than the maximum (11): '
                      'could not convert to maximum_distance:',
                      str(ctx.exception))


def sitemodel():
    return [BytesIO(b'''\
<?xml version="1.0" encoding="utf-8"?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
    <siteModel>
        <site lon="0.0" lat="0.0" vs30="1200.0" vs30Type="inferred" z1pt0="100.0" z2pt5="2.0" backarc="False" />
        <site lon="0.0" lat="0.1" vs30="600.0" vs30Type="inferred" z1pt0="100.0" z2pt5="2.0" backarc="True" />
        <site lon="0.0" lat="0.2" vs30="200.0" vs30Type="inferred" z1pt0="100.0" z2pt5="2.0" backarc="False" />
    </siteModel>
</nrml>''')]


class ExposureTestCase(unittest.TestCase):
    exposure = general.gettemp('''\
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
</nrml>''', suffix='.xml')

    exposure0 = general.gettemp('''\
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
</nrml>''', suffix='.xml')

    exposure1 = general.gettemp('''\
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
</nrml>''', suffix='.xml')

    exposure2 = general.gettemp('''\
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
</nrml>''', suffix='.xml')  # wrong cost type "aggregate"

    exposure3 = general.gettemp('''\
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
      <asset id="a1" taxonomy="RM " number="3000">
        <location lon="81.2985" lat="29.1098"/>
        <costs>
          <cost type="structural" value="1000"/>
        </costs>
      </asset>
    </assets>
  </exposureModel>
</nrml>''', suffix='.xml')

    exposure4 = general.gettemp('''\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4">
  <exposureModel id="ep" category="buildings">
    <description>Exposure model for buildings</description>
    <conversions>
       <costTypes name="structural" type="aggregated" unit="USD"/>
    </conversions>
    <assets>
      <asset id="a1" taxonomy="RM" number="3000">
        <location lon="81.2985" lat="29.1098"/>
        <costs>
          <cost type="structural" value="1000"/>
        </costs>
      </asset>
    </assets>
  </exposureModel>
</nrml>''', suffix='.xml')

    def test_get_metadata(self):
        [exp] = asset.Exposure.read_headers([self.exposure])
        self.assertEqual(exp.description, 'Exposure model for buildings')
        self.assertEqual([tuple(ct) for ct in exp.cost_types],
                         [('structural', 'per_asset', 'USD')])

    def test_missing_number(self):
        raise unittest.SkipTest
        oqparam = mock.Mock()
        oqparam.base_path = '/'
        oqparam.calculation_mode = 'scenario_damage'
        oqparam.all_cost_types = ['occupants']
        oqparam.inputs = {'exposure': [self.exposure]}
        oqparam.region = '''\
POLYGON((78.0 31.5, 89.5 31.5, 89.5 25.5, 78.0 25.5, 78.0 31.5))'''
        oqparam.time_event = None
        oqparam.ignore_missing_costs = []
        oqparam.aggregate_by = []

        with self.assertRaises(Exception) as ctx:
            readinput.get_exposure(oqparam)
        self.assertIn("node asset: 'number', line 17 of", str(ctx.exception))

    def test_zero_number(self):
        oqparam = mock.Mock()
        oqparam.base_path = '/'
        oqparam.calculation_mode = 'scenario_damage'
        oqparam.all_cost_types = ['structural']
        oqparam.insured_losses = False
        oqparam.inputs = {'exposure': [self.exposure0]}
        oqparam.region = '''\
POLYGON((78.0 31.5, 89.5 31.5, 89.5 25.5, 78.0 25.5, 78.0 31.5))'''
        oqparam.time_event = None
        oqparam.ignore_missing_costs = []
        oqparam.aggregate_by = []

        with self.assertRaises(ValueError) as ctx:
            readinput.get_exposure(oqparam)
        self.assertIn("Could not convert number->compose"
                      "(positivefloat,nonzero): '0' is zero, line 17",
                      str(ctx.exception))

    def test_invalid_asset_id(self):
        oqparam = mock.Mock()
        oqparam.base_path = '/'
        oqparam.calculation_mode = 'scenario_damage'
        oqparam.all_cost_types = ['structural']
        oqparam.inputs = {'exposure': [self.exposure1]}
        oqparam.region = '''\
POLYGON((78.0 31.5, 89.5 31.5, 89.5 25.5, 78.0 25.5, 78.0 31.5))'''
        oqparam.time_event = None
        oqparam.ignore_missing_costs = []
        oqparam.aggregate_by = []
        with self.assertRaises(ValueError) as ctx:
            readinput.get_exposure(oqparam)
        self.assertIn("Invalid ID 'a 1': the only accepted chars are "
                      "a-zA-Z0-9_-, line 11", str(ctx.exception))

    def test_no_assets(self):
        oqparam = mock.Mock()
        oqparam.base_path = '/'
        oqparam.calculation_mode = 'scenario_risk'
        oqparam.all_cost_types = ['structural']
        oqparam.insured_losses = True
        oqparam.inputs = {'exposure': [self.exposure],
                          'structural_vulnerability': None}
        oqparam.region = '''\
POLYGON((68.0 31.5, 69.5 31.5, 69.5 25.5, 68.0 25.5, 68.0 31.5))'''
        oqparam.time_event = None
        oqparam.ignore_missing_costs = []
        oqparam.aggregate_by = []
        with self.assertRaises(RuntimeError) as ctx:
            readinput.get_exposure(oqparam)
        self.assertIn('Could not find any asset within the region!',
                      str(ctx.exception))

    def test_wrong_cost_type(self):
        oqparam = mock.Mock()
        oqparam.base_path = '/'
        oqparam.calculation_mode = 'scenario_risk'
        oqparam.all_cost_types = ['structural']
        oqparam.ignore_missing_costs = []
        oqparam.region = '''\
POLYGON((68.0 31.5, 69.5 31.5, 69.5 25.5, 68.0 25.5, 68.0 31.5))'''
        oqparam.inputs = {'exposure': [self.exposure2],
                          'structural_vulnerability': None}
        oqparam.aggregate_by = []
        with self.assertRaises(ValueError) as ctx:
            readinput.get_exposure(oqparam)
        self.assertIn("Got 'aggregate', expected "
                      "aggregated|per_area|per_asset, line 7",
                      str(ctx.exception))

    def test_invalid_taxonomy(self):
        oqparam = mock.Mock()
        oqparam.base_path = '/'
        oqparam.calculation_mode = 'scenario_damage'
        oqparam.all_cost_types = ['structural']
        oqparam.inputs = {'exposure': [self.exposure3]}
        oqparam.region = '''\
POLYGON((78.0 31.5, 89.5 31.5, 89.5 25.5, 78.0 25.5, 78.0 31.5))'''
        oqparam.time_event = None
        oqparam.insured_losses = False
        oqparam.ignore_missing_costs = []
        oqparam.aggregate_by = []
        with self.assertRaises(ValueError) as ctx:
            readinput.get_exposure(oqparam)
        self.assertIn("'RM ' contains whitespace chars, line 11",
                      str(ctx.exception))

    def test_missing_cost_types(self):
        job_ini = general.gettemp('''\
[general]
description = Exposure with missing cost_types
calculation_mode = scenario
exposure_file = %s''' % os.path.basename(self.exposure4))
        oqparam = readinput.get_oqparam(job_ini)
        with self.assertRaises(InvalidFile) as ctx:
            readinput.get_sitecol_assetcol(oqparam, cost_types=['structural'])
        self.assertIn("is missing", str(ctx.exception))


class GetCompositeSourceModelTestCase(unittest.TestCase):
    # test the case in_memory=False, used when running `oq info job.ini`

    def test_nrml04(self):
        oq = readinput.get_oqparam('job.ini', case_1)
        csm = readinput.get_composite_source_model(oq, in_memory=False)
        srcs = csm.get_sources()  # a single PointSource
        self.assertEqual(len(srcs), 1)

    def test_nrml05(self):
        oq = readinput.get_oqparam('job.ini', case_2)
        csm = readinput.get_composite_source_model(oq, in_memory=False)
        srcs = csm.get_sources()  # two PointSources
        self.assertEqual(len(srcs), 2)

    def test_reduce_source_model(self):
        case2 = os.path.dirname(case_2.__file__)
        smlt = os.path.join(case2, 'source_model_logic_tree.xml')
        readinput.reduce_source_model(smlt, [], False)

    def test_wrong_trts(self):
        # invalid TRT in job.ini [reqv]
        oq = readinput.get_oqparam('job.ini', case_2)
        fname = oq.inputs['reqv'].pop('active shallow crust')
        oq.inputs['reqv']['act shallow crust'] = fname
        with self.assertRaises(ValueError) as ctx:
            readinput.get_composite_source_model(oq, in_memory=False)
        self.assertIn('Unknown TRT=act shallow crust', str(ctx.exception))

    def test_applyToSources(self):
        oq = readinput.get_oqparam('job.ini', case_21)
        with mock.patch('logging.info') as info:
            readinput.get_composite_source_model(oq)
        self.assertEqual(
            info.call_args[0],
            ('Applied %d changes to the composite source model', 81))

    def test_extra_large_source(self):
        oq = readinput.get_oqparam('job.ini', case_21)
        with mock.patch('logging.error') as error, datastore.hdf5new() as h5:
            with mock.patch('openquake.hazardlib.geo.utils.MAX_EXTENT', 80):
                readinput.get_composite_source_model(oq, h5)
                os.remove(h5.filename)
        self.assertEqual(
            error.call_args[0][0], 'source SFLT2: too large: 84 km')


class GetCompositeRiskModelTestCase(unittest.TestCase):
    def tearDown(self):
        # cleanup evil global
        readinput.exposure = None

    def test_missing_vulnerability_function(self):
        oq = readinput.get_oqparam('job.ini', case_caracas)
        with self.assertRaises(ValidationError):
            readinput.get_risk_model(oq)


class SitecolAssetcolTestCase(unittest.TestCase):

    def tearDown(self):
        # cleanup evil global
        readinput.exposure = None

    def test_grid_site_model_exposure(self):
        oq = readinput.get_oqparam(
            'job.ini', case_16, region_grid_spacing='15')
        sitecol, assetcol, discarded = readinput.get_sitecol_assetcol(oq)
        self.assertEqual(len(sitecol), 141)  # 10 sites were discarded silently
        self.assertEqual(len(assetcol), 151)
        self.assertEqual(len(discarded), 0)  # no assets were discarded

    def test_site_model_exposure(self):
        oq = readinput.get_oqparam('job.ini', case_16)
        sitecol, assetcol, discarded = readinput.get_sitecol_assetcol(oq)
        self.assertEqual(len(sitecol), 148)
        self.assertEqual(len(assetcol), 151)
        self.assertEqual(len(discarded), 0)

    def test_site_model_sites(self):
        # you cannot set them at the same time
        with self.assertRaises(ValueError):
            readinput.get_oqparam('job.ini', case_16, sites='0 0')
