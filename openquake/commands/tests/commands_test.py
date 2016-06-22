# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2016 GEM Foundation
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
import sys
import mock
import shutil
import tempfile
import unittest

from openquake.baselib.general import writetmp
from openquake import commonlib
from openquake.calculators.tests import check_platform
from openquake.commands.info import info
from openquake.commands.tidy import tidy
from openquake.commands.show import show
from openquake.commands.show_attrs import show_attrs
from openquake.commands.export import export
from openquake.commands.reduce import reduce
from openquake.commands import run
from openquake.commands.upgrade_nrml import get_vulnerability_functions_04
from openquake.qa_tests_data.classical import case_1
from openquake.qa_tests_data.classical_risk import case_3
from openquake.qa_tests_data.scenario import case_4
from openquake.qa_tests_data.event_based import case_5

DATADIR = os.path.join(commonlib.__path__[0], 'tests', 'data')


class Print(object):
    def __init__(self):
        self.lst = []

    def __call__(self, *args):
        self.lst.append(' '.join(map(bytes, args)))

    def __str__(self):
        return u'\n'.join(self.lst).decode('utf-8')

    @classmethod
    def patch(cls):
        bprint = 'builtins.print' if sys.version > '3' else '__builtin__.print'
        return mock.patch(bprint, cls())


class InfoTestCase(unittest.TestCase):
    EXPECTED = '''<CompositionInfo
b1, x15.xml, trt=[0], weight=1.00: 1 realization(s)>
See https://github.com/gem/oq-risklib/blob/master/doc/effective-realizations.rst for an explanation
<RlzsAssoc(size=1, rlzs=1)
0,AkkarBommer2010(): ['<0,b1~@_AkkarBommer2010_@_@_@_@_@,w=1.0>']>
=============== ======
attribute       nbytes
=============== ======'''

    def test_zip(self):
        path = os.path.join(DATADIR, 'frenchbug.zip')
        with Print.patch() as p:
            info(None, None, None, None, None, None, path)
        self.assertEqual(self.EXPECTED, str(p)[:len(self.EXPECTED)])

    # poor man tests: checking that the flags produce a few characters
    # (more than 10) and do not break; I am not checking the precise output

    def test_calculators(self):
        with Print.patch() as p:
            info(True, None, None, None, None, '')
        self.assertGreater(len(str(p)), 10)

    def test_gsims(self):
        with Print.patch() as p:
            info(None, True, None, None, None, '')
        self.assertGreater(len(str(p)), 10)

    def test_views(self):
        with Print.patch() as p:
            info(None, None, True, None, None, '')
        self.assertGreater(len(str(p)), 10)

    def test_exports(self):
        with Print.patch() as p:
            info(None, None, None, True, None, '')
        self.assertGreater(len(str(p)), 10)

    # NB: info --report is tested manually once in a while


class TidyTestCase(unittest.TestCase):
    def test_ok(self):
        fname = writetmp('''\
<?xml version="1.0" encoding="utf-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"
      xmlns:gml="http://www.opengis.net/gml">
<gmfCollection gsimTreePath="" sourceModelTreePath="">
  <gmfSet stochasticEventSetId="1">
    <gmf IMT="PGA" ruptureId="scenario-0">
      <node gmv="0.0126515007046" lon="12.12477995" lat="43.5812"/>
      <node gmv="0.0124056290492" lon="12.12478193" lat="43.5812"/>
    </gmf>
  </gmfSet>
</gmfCollection>
</nrml>''', suffix='.xml')
        with Print.patch() as p:
            tidy([fname])
        self.assertIn('Reformatted', str(p))
        self.assertEqual(open(fname).read(), '''\
<?xml version="1.0" encoding="utf-8"?>
<nrml
xmlns="http://openquake.org/xmlns/nrml/0.5"
xmlns:gml="http://www.opengis.net/gml"
>
    <gmfCollection
    gsimTreePath=""
    sourceModelTreePath=""
    >
        <gmfSet
        stochasticEventSetId="1"
        >
            <gmf
            IMT="PGA"
            ruptureId="scenario-0"
            >
                <node gmv="1.2651501E-02" lat="4.3581200E+01" lon="1.2124780E+01"/>
                <node gmv="1.2405629E-02" lat="4.3581200E+01" lon="1.2124780E+01"/>
            </gmf>
        </gmfSet>
    </gmfCollection>
</nrml>
''')

    def test_invalid(self):
        fname = writetmp('''\
<?xml version="1.0" encoding="utf-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"
      xmlns:gml="http://www.opengis.net/gml">
<gmfCollection gsimTreePath="" sourceModelTreePath="">
  <gmfSet stochasticEventSetId="1">
    <gmf IMT="PGA" ruptureId="scenario-0">
      <node gmv="0.012646" lon="12.12477995" lat="43.5812"/>
      <node gmv="-0.012492" lon="12.12478193" lat="43.5812"/>
    </gmf>
  </gmfSet>
</gmfCollection>
</nrml>''', suffix='.xml')
        with Print.patch() as p:
            tidy([fname])
        self.assertIn('Could not convert gmv->positivefloat: '
                      'float -0.012492 < 0, line 8 of', str(p))


class RunShowExportTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Build a datastore instance to show what it is inside
        """
        # the tests here gives mysterious core dumps in Ubuntu 16.04,
        # but only if called together with all other tests with the command
        # nosetests openquake/commonlib/
        check_platform('trusty')
        job_ini = os.path.join(os.path.dirname(case_1.__file__), 'job.ini')
        with Print.patch() as cls.p:
            calc = run._run(job_ini, 0, False, 'info', None, '', {})
        cls.calc_id = calc.datastore.calc_id

    def test_run_calc(self):
        self.assertIn('See the output with hdfview', str(self.p))

    def test_show_calc(self):
        # test show all
        with Print.patch() as p:
            show('all')
        with Print.patch() as p:
            show('contents', self.calc_id)
        self.assertIn('sitecol', str(p))

        with Print.patch() as p:
            show('sitecol', self.calc_id)
        self.assertEqual(str(p), '<SiteCollection with 1 sites>')

    def test_show_attrs(self):
        with Print.patch() as p:
            show_attrs('hcurve', self.calc_id)
        self.assertEqual("'hcurve' is not in <DataStore %d>" %
                         self.calc_id, str(p))
        with Print.patch() as p:
            show_attrs('hcurves', self.calc_id)
        self.assertEqual("imtls [['PGA' '3']\n ['SA(0.1)' '3']]\nnbytes 48",
                         str(p))

    def test_export_calc(self):
        tempdir = tempfile.mkdtemp()
        with Print.patch() as p:
            export('hcurves', tempdir, self.calc_id)
        [fname] = os.listdir(tempdir)
        self.assertIn(str(fname), str(p))
        shutil.rmtree(tempdir)


class ReduceTestCase(unittest.TestCase):
    TESTDIR = os.path.dirname(case_3.__file__)

    def test_exposure(self):
        tempdir = tempfile.mkdtemp()
        dest = os.path.join(tempdir, 'exposure_model.xml')
        shutil.copy(os.path.join(self.TESTDIR, 'exposure_model.xml'), dest)
        with Print.patch() as p:
            reduce(dest, 0.5)
        self.assertIn('Extracted 8 nodes out of 13', str(p))
        shutil.rmtree(tempdir)

    def test_source_model(self):
        tempdir = tempfile.mkdtemp()
        dest = os.path.join(tempdir, 'source_model.xml')
        shutil.copy(os.path.join(self.TESTDIR, 'source_model.xml'), tempdir)
        with Print.patch() as p:
            reduce(dest, 0.5)
        self.assertIn('Extracted 9 nodes out of 15', str(p))
        shutil.rmtree(tempdir)

    def test_site_model(self):
        testdir = os.path.dirname(case_4.__file__)
        tempdir = tempfile.mkdtemp()
        dest = os.path.join(tempdir, 'site_model.xml')
        shutil.copy(os.path.join(testdir, 'site_model.xml'), tempdir)
        with Print.patch() as p:
            reduce(dest, 0.5)
        self.assertIn('Extracted 2 nodes out of 3', str(p))
        shutil.rmtree(tempdir)

    def test_sites_csv(self):
        testdir = os.path.dirname(case_5.__file__)
        tempdir = tempfile.mkdtemp()
        dest = os.path.join(tempdir, 'sites.csv')
        shutil.copy(os.path.join(testdir, 'sites.csv'), tempdir)
        with Print.patch() as p:
            reduce(dest, 0.5)
        self.assertIn('Extracted 50 lines out of 100', str(p))
        shutil.rmtree(tempdir)


class UpgradeNRMLTestCase(unittest.TestCase):
    vf = writetmp('''\
<?xml version="1.0"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4" xmlns:gml="http://www.opengis.net/gml">
    <vulnerabilityModel>
        <discreteVulnerabilitySet vulnerabilitySetID="vm1" assetCategory="buildings" lossCategory="Economic_loss">
            <IML IMT="PGA">0.01	0.040408163	0.070816327	0.10122449	0.131632653	0.162040816	0.19244898	0.222857143	0.253265306	0.283673469	0.314081633	0.344489796	0.374897959	0.405306122	0.435714286	0.466122449	0.496530612	0.526938776	0.557346939	0.587755102	0.618163265	0.648571429	0.678979592	0.709387755	0.739795918	0.770204082	0.800612245	0.831020408	0.861428571	0.891836735	0.922244898	0.952653061	0.983061224	1.013469388	1.043877551	1.074285714	1.104693878	1.135102041	1.165510204	1.195918367	1.226326531	1.256734694	1.287142857	1.31755102	1.347959184	1.378367347	1.40877551	1.439183673	1.469591837	1.5 </IML>
            <discreteVulnerability vulnerabilityFunctionID="A-SPSB-1" probabilisticDistribution="LN">
                   <lossRatio>0	0.000409057	0.018800826	0.196366309	0.709345589	0.991351187	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1</lossRatio>
                  <coefficientsVariation>0	0.000509057	0.022010677	0.186110985	0.241286071	0.010269671	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0 </coefficientsVariation>
            </discreteVulnerability>
			<discreteVulnerability vulnerabilityFunctionID="MC-RCSB-1" probabilisticDistribution="LN">
                   <lossRatio>0	0	0.000354248	0.002180043	0.006848174	0.01748566	0.044583318	0.091324846	0.159173631	0.253517121	0.373268448	0.505832577	0.645493182	0.770135164	0.86646734	0.936052661	0.976841975	0.990830255	0.997607079	0.999672011	0.999965458	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1</lossRatio>
                  <coefficientsVariation>0	0	0.000425098	0.002589524	0.008105089	0.020649985	0.050748113	0.097556125	0.158686273	0.224491958	0.271934549	0.29042741	0.273137491	0.206451463	0.134850893	0.071066913	0.027049667	0.01083137	0.002925074	0.000491983	5.18136E-05	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0</coefficientsVariation>
            </discreteVulnerability>
			<discreteVulnerability vulnerabilityFunctionID="MC-RCSM-4" probabilisticDistribution="LN">
                   <lossRatio>0.0	0.00056	0.00544	0.02529	0.07808	0.19369	0.39686	0.64727	0.85844	0.96782	0.99686	0.99985	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0	1.0</lossRatio>
                  <coefficientsVariation>0	0.00071	0.00643	0.02956	0.08625	0.18633	0.28294	0.26860	0.14376	0.03717	0.00371	0.00006	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0</coefficientsVariation>
            </discreteVulnerability>
			<discreteVulnerability vulnerabilityFunctionID="MC-RLSB-2" probabilisticDistribution="LN">
                   <lossRatio>0	0.00008	0.00129	0.00685	0.02531	0.07019	0.15554	0.28234	0.44819	0.63240	0.79655	0.91125	0.97161	0.99395	0.99922	0.99997	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1</lossRatio>
                  <coefficientsVariation>0	0.00012	0.00161	0.00821	0.02945	0.07804	0.15657	0.24136	0.29537	0.27835	0.19298	0.09629	0.03286	0.00726	0.00088	0.00005	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0</coefficientsVariation>
            </discreteVulnerability>
			<discreteVulnerability vulnerabilityFunctionID="MR-RCSB-2" probabilisticDistribution="LN">
                   <lossRatio>0	0.00018	0.00158	0.00622	0.01735	0.03921	0.07533	0.13304	0.21241	0.31687	0.43838	0.56868	0.69506	0.80516	0.88805	0.94528	0.97595	0.99150	0.99749	0.99937	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1</lossRatio>
                  <coefficientsVariation>0	0.00027	0.00201	0.00754	0.02036	0.04522	0.08357	0.13765	0.20040	0.25794	0.29400	0.29247	0.25234	0.18783	0.11861	0.06214	0.02807	0.01022	0.00302	0.00086	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0</coefficientsVariation>
            </discreteVulnerability>
			<discreteVulnerability vulnerabilityFunctionID="MR-SLSB-1" probabilisticDistribution="LN">
                   <lossRatio>0	0	0.00009	0.00060	0.00239	0.00699	0.01668	0.03520	0.07229	0.11251	0.16055	0.21886	0.28725	0.36604	0.45110	0.53857	0.62520	0.70771	0.78218	0.84378	0.89355	0.93179	0.95940	0.97786	0.98814	0.99406	0.99734	0.99896	0.99963	0.99988	0.99997	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1</lossRatio>
                  <coefficientsVariation>0	0	0	0.00064	0.00281	0.00824	0.01954	0.04083	0.07997	0.11907	0.16040	0.20359	0.24522	0.27727	0.29427	0.29472	0.27841	0.24698	0.20391	0.15694	0.11320	0.07588	0.04670	0.02598	0.01399	0.00714	0.00323	0.00124	0.00054	0.00005	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0</coefficientsVariation>
            </discreteVulnerability>
        </discreteVulnerabilitySet>
    </vulnerabilityModel>
</nrml>''')

    def test(self):
        get_vulnerability_functions_04(self.vf)
        # NB: look also at nrml.get_vulnerability_functions_04
