# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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

import io
import os
import re
import sys
import unittest.mock as mock
from contextlib import redirect_stdout
import shutil
import zipfile
import tempfile
import unittest
import numpy

from pathlib import Path

from openquake.baselib.python3compat import encode
from openquake.baselib.general import gettemp, chdir
from openquake.baselib import parallel, sap
from openquake.baselib.hdf5 import read_csv
from openquake.baselib.tests.flake8_test import check_newlines
from openquake.hazardlib import tests
from openquake import commonlib
from openquake.commonlib.datastore import read
from openquake.commonlib.readinput import get_params
from openquake.engine.engine import create_jobs, run_jobs
from openquake.commands.tests.data import to_reduce
from openquake.calculators.views import view
from openquake.qa_tests_data.event_based_damage import case_15
from openquake.qa_tests_data.logictree import case_09, case_13, case_56
from openquake.qa_tests_data.classical import case_01, case_18
from openquake.qa_tests_data.classical_risk import case_3
from openquake.qa_tests_data.scenario import case_4
from openquake.qa_tests_data.event_based import (
    case_1 as eb_case_1, case_5, case_16, case_21)
from openquake.qa_tests_data.event_based_risk import (
    case_master, case_1 as case_eb)
from openquake.qa_tests_data.scenario import case_25
from openquake.qa_tests_data.scenario_risk import case_shapefile, case_shakemap
from openquake.qa_tests_data.gmf_ebrisk import case_1 as ebrisk
from openquake.server.tests import data as test_data

DATADIR = os.path.join(commonlib.__path__[0], 'tests', 'data')
NRML_DIR = os.path.dirname(tests.__file__)
MIXED_SRC_MODEL = os.path.join(
    NRML_DIR, 'source_model/mixed.xml')
AREA_SOURCE_SRC_MODEL = os.path.join(
    NRML_DIR, 'source_model/area-source.xml')
COMPLEX_FAULT_SRC_MODEL = os.path.join(
    NRML_DIR, 'source_model/complex-fault-source.xml')
MULTI_POINT_SRC_MODEL = os.path.join(
    NRML_DIR, 'source_model/multi-point-source.xml')
POINT_SRC_MODEL = os.path.join(
    NRML_DIR, 'source_model/point-source.xml')
SIMPLE_FAULT_SRC_MODEL = os.path.join(
    NRML_DIR, 'source_model/simple-fault-source.xml')


def setup_module():
    os.environ['OQ_DATABASE'] = 'local'


class Print(object):
    def __init__(self):
        self.lst = []

    def __call__(self, *args, **kw):
        self.lst.append(b' '.join(encode(str(a)) for a in args))

    def __str__(self):
        return b'\n'.join(self.lst).decode('utf-8')

    @classmethod
    def patch(cls):
        return mock.patch('builtins.print', cls())


class InfoTestCase(unittest.TestCase):

    def test_zip(self):
        path = os.path.join(DATADIR, 'frenchbug.zip')
        with Print.patch() as p:
            sap.runline(f'openquake.commands info {path}')
        self.assertIn('input size', str(p))

    # poor man tests: checking that the flags produce a few characters
    # (more than 10) and do not break; I am not checking the precise output

    def test_calculators(self):
        with Print.patch() as p:
            sap.runline('openquake.commands info calculators')
        self.assertGreater(len(str(p)), 10)

    def test_gsims(self):
        with Print.patch() as p:
            sap.runline('openquake.commands info gsims')
        self.assertGreater(len(str(p)), 10)

    def test_imts(self):
        with Print.patch() as p:
            sap.runline('openquake.commands info imts')
        self.assertGreaterEqual(len(str(p)), 18)

    def test_views(self):
        with Print.patch() as p:
            sap.runline('openquake.commands info views')
        self.assertGreater(len(str(p)), 10)

    def test_exports(self):
        with Print.patch() as p:
            sap.runline('openquake.commands info exports')
        self.assertGreater(len(str(p)), 10)

    def test_extracts(self):
        with Print.patch() as p:
            sap.runline('openquake.commands info extracts')
        self.assertGreater(len(str(p)), 10)

    def test_parameters(self):
        with Print.patch() as p:
            sap.runline('openquake.commands info parameters')
        self.assertGreater(len(str(p)), 10)

    def test_mfds(self):
        with Print.patch() as p:
            sap.runline('openquake.commands info mfds')
        lines = str(p).split()
        self.assertGreaterEqual(len(lines), 5)

    def test_cfg(self):
        with Print.patch() as p:
            sap.runline('openquake.commands info cfg')
        lines = str(p).split('\n')
        self.assertGreaterEqual(len(lines), 2)

    def test_sources(self):
        with Print.patch() as p:
            sap.runline('openquake.commands info sources')
        lines = str(p).split()
        self.assertGreaterEqual(len(lines), 9)

    def test_job_ini(self):
        path = os.path.join(os.path.dirname(case_09.__file__), 'job.ini')
        with Print.patch() as p:
            sap.runline('openquake.commands info ' + path)
        self.assertIn('Classical Hazard QA Test, Case 9', str(p))

    def test_logictree(self):
        path = os.path.join(os.path.dirname(case_09.__file__),
                            'source_model_logic_tree.xml')
        with Print.patch() as p:
            sap.runline('openquake.commands info ' + path)
        self.assertIn('pointSource', str(p))

    def test_report(self):
        path = os.path.join(os.path.dirname(case_09.__file__), 'job.ini')
        save = 'openquake.calculators.reportwriter.ReportWriter.save'
        with Print.patch() as p, mock.patch(save, lambda self, fname: None):
            sap.runline('openquake.commands info --report ' + path)
        self.assertIn('report.rst', str(p))

    def test_report_ebr(self):
        path = os.path.join(os.path.dirname(case_16.__file__), 'job.ini')
        save = 'openquake.calculators.reportwriter.ReportWriter.save'
        with Print.patch() as p, mock.patch(save, lambda self, fname: None):
            sap.runline('openquake.commands info -r ' + path)
        self.assertIn('report.rst', str(p))

    def test_consequences(self):
        with Print.patch() as p:
            sap.runline('openquake.commands info consequences')
        self.assertIn('consequences are implemented', str(p))


class TidyTestCase(unittest.TestCase):
    def test_ok(self):
        fname = gettemp('''\
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
</nrml>''', suffix='.xml')
        with Print.patch() as p:
            sap.runline('openquake.commands tidy ' + fname)
        self.assertIn('Reformatted', str(p))
        self.assertEqual(open(fname).read(), '''\
<?xml version="1.0" encoding="utf-8"?>
<nrml
xmlns="http://openquake.org/xmlns/nrml/0.4"
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
            ruptureId="0"
            >
                <node gmv="1.26515E-02" lat="4.35812E+01" lon="1.21248E+01"/>
                <node gmv="1.24056E-02" lat="4.35812E+01" lon="1.21248E+01"/>
            </gmf>
        </gmfSet>
    </gmfCollection>
</nrml>
''')

    def test_invalid(self):
        fname = gettemp('''\
<?xml version="1.0" encoding="utf-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"
      xmlns:gml="http://www.opengis.net/gml">
<gmfCollection gsimTreePath="" sourceModelTreePath="">
  <gmfSet stochasticEventSetId="1">
    <gmf IMT="PGA" ruptureId="0">
      <node gmv="0.012646" lon="12.12477995" lat="43.5812"/>
      <node gmv="-0.012492" lon="12.12478193" lat="43.5812"/>
    </gmf>
  </gmfSet>
</gmfCollection>
</nrml>''', suffix='.xml')
        with Print.patch() as p:
            sap.runline('openquake.commands tidy ' + fname)
        self.assertIn('Could not convert gmv->positivefloat: '
                      'float -0.012492 < 0, line 8', str(p))


class RunShowExportTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Build a datastore instance to show what it is inside
        """
        job_ini = os.path.join(os.path.dirname(case_01.__file__), 'job.ini')
        with Print.patch() as cls.p:
            calc = sap.runline(f'openquake.commands run {job_ini} -c 0')
        cls.calc_id = calc.datastore.calc_id

    def test_run_calc(self):
        self.assertIn('See the output with silx view', str(self.p))

    def test_show_calc(self):
        with Print.patch() as p:
            sap.runline('openquake.commands show contents %d' % self.calc_id)
        self.assertIn('sitecol', str(p))

        with Print.patch() as p:
            sap.runline('openquake.commands show sitecol %d' % self.calc_id)
        self.assertIn('sids | lon     | lat | depth | vs30  | vs30measured',
                      str(p))

        with Print.patch() as p:
            sap.runline(f'openquake.commands show slow_sources {self.calc_id}')
        self.assertIn('source_id | code | calc_time | num_sites', str(p))

    def test_show_attrs(self):
        with Print.patch() as p:
            sap.runline(
                f'openquake.commands show_attrs sitecol {self.calc_id}')
        self.assertEqual('__pdcolumns__ sids lon lat depth vs30 vs30measured\n'
                         '__pyclass__ openquake.hazardlib.site.SiteCollection',
                         str(p))

    def test_show_oqparam(self):
        with Print.patch() as p:
            sap.runline(f'openquake.commands show oqparam {self.calc_id}')
        self.assertIn('"inputs": {', str(p))

    def test_export_calc(self):
        tempdir = tempfile.mkdtemp()
        with Print.patch() as p:
            sap.runline(f'openquake.commands export hcurves {self.calc_id}'
                        f' -e csv --export-dir={tempdir}')
        fnames = os.listdir(tempdir)
        self.assertIn(str(fnames[0]), str(p))
        shutil.rmtree(tempdir)

    def test_extract_sitecol(self):
        tempdir = tempfile.mkdtemp()
        with Print.patch() as p:
            sap.runline("openquake.commands extract sitecol "
                        f"{self.calc_id} --extract-dir={tempdir}")
        fnames = os.listdir(tempdir)
        self.assertIn(str(fnames[0]), str(p))
        shutil.rmtree(tempdir)

    def test_extract_ruptures(self):
        job_ini = os.path.join(
            os.path.dirname(eb_case_1.__file__), 'job_ruptures.ini')
        with Print.patch():
            calc = sap.runline(f'openquake.commands run {job_ini} -c 0')
        calc_id = calc.datastore.calc_id
        tempdir = tempfile.mkdtemp()
        with Print.patch():
            sap.runline("openquake.commands extract ruptures "
                        f"{calc_id} --extract-dir={tempdir}")
        fnames = os.listdir(tempdir)
        fname = os.path.join(tempdir, fnames[0])
        error = check_newlines(open(fname, 'rb').read())
        if error:
            raise ValueError(
                f'Invalid newlines in the exported ruptures file {fname}')
        else:
            shutil.rmtree(tempdir)


class CompareTestCase(unittest.TestCase):
    def test_med_gmv(self):
        # testing the postprocessor med_gmv
        ini = os.path.join(os.path.dirname(case_13.__file__), 'job_gmv.ini')
        [job] = run_jobs(create_jobs([ini]))
        id = job.calc_id
        with Print.patch() as p:
            sap.runline(f"openquake.commands compare med_gmv PGA {id} {id}")
        self.assertIn('0_0!aFault_aPriori_D2_1: no differences within '
                      'the tolerances', str(p))


class SampleSmTestCase(unittest.TestCase):
    TESTDIR = os.path.dirname(case_3.__file__)

    def test_exposure(self):
        tempdir = tempfile.mkdtemp()
        dest = os.path.join(tempdir, 'exposure_model.xml')
        shutil.copy(os.path.join(self.TESTDIR, 'exposure_model.xml'), dest)
        with Print.patch() as p:
            sap.runline(f'openquake.commands sample {dest} 0.5')
        self.assertIn('Extracted 8 nodes out of 13', str(p))

        # check the exposure is still valid
        sap.runline(f'openquake.commands check_input {dest}')
        shutil.rmtree(tempdir)

    def test_source_model(self):
        tempdir = tempfile.mkdtemp()
        dest = os.path.join(tempdir, 'source_model.xml')
        shutil.copy(os.path.join(self.TESTDIR, 'source_model.xml'), tempdir)
        with Print.patch() as p:
            sap.runline(f'openquake.commands sample {dest} 0.5')
        self.assertIn('Extracted 9 nodes out of 15', str(p))
        shutil.rmtree(tempdir)

    def test_site_model(self):
        testdir = os.path.dirname(case_4.__file__)
        tempdir = tempfile.mkdtemp()
        dest = os.path.join(tempdir, 'site_model.xml')
        shutil.copy(os.path.join(testdir, 'site_model.xml'), tempdir)
        with Print.patch() as p:
            sap.runline(f'openquake.commands sample {dest} 0.5')
        self.assertIn('Extracted 2 nodes out of 3', str(p))
        shutil.rmtree(tempdir)

    def test_sites_csv(self):
        testdir = os.path.dirname(case_5.__file__)
        tempdir = tempfile.mkdtemp()
        dest = os.path.join(tempdir, 'sites.csv')
        shutil.copy(os.path.join(testdir, 'sites.csv'), tempdir)
        with Print.patch() as p:
            sap.runline(f'openquake.commands sample {dest} 0.5')
        self.assertIn('Extracted 50 lines out of 99', str(p))
        shutil.rmtree(tempdir)


class UpgradeNRMLTestCase(unittest.TestCase):
    def test(self):
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, 'vf.xml')
        with open(path, 'w') as f:
            f.write('''\
<?xml version="1.0"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4" xmlns:gml="http://www.opengis.net/gml">
    <vulnerabilityModel>
        <discreteVulnerabilitySet vulnerabilitySetID="vm1" assetCategory="buildings" lossCategory="Economic_loss">
            <IML IMT="PGA">0.01	0.040408163	0.070816327	0.10122449	0.131632653	0.162040816	0.19244898	0.222857143	0.253265306	0.283673469	0.314081633	0.344489796	0.374897959	0.405306122	0.435714286	0.466122449	0.496530612	0.526938776	0.557346939	0.587755102	0.618163265	0.648571429	0.678979592	0.709387755	0.739795918	0.770204082	0.800612245	0.831020408	0.861428571	0.891836735	0.922244898	0.952653061	0.983061224	1.013469388	1.043877551	1.074285714	1.104693878	1.135102041	1.165510204	1.195918367	1.226326531	1.256734694	1.287142857	1.31755102	1.347959184	1.378367347	1.40877551	1.439183673	1.469591837	1.5 </IML>
            <discreteVulnerability vulnerabilityFunctionID="A-SPSB-1" probabilisticDistribution="LN">
                   <lossRatio>0	0.000409057	0.018800826	0.196366309	0.709345589	0.991351187	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1	1</lossRatio>
                  <coefficientsVariation>0	0.000509057	0.022010677	0.186110985	0.241286071	0.010269671	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0 </coefficientsVariation>
            </discreteVulnerability>
        </discreteVulnerabilitySet>
    </vulnerabilityModel>
</nrml>''')
        sap.runline(f'openquake.commands upgrade_nrml {tmpdir}')
        if not sys.platform.startswith('win'):
            # NOTE: on Windows it raises:
            #       PermissionError: [WinError 32] The process cannot access
            #       the file because it is being used by another process
            shutil.rmtree(tmpdir)


class ZipTestCase(unittest.TestCase):
    """
    Test for the command oq zip
    """

    def test_zip(self):
        # this is a case with .hdf5 files
        ini = os.path.join(os.path.dirname(case_18.__file__), 'job.ini')
        dtemp = tempfile.mkdtemp()
        xzip = os.path.join(dtemp, 'x.zip')
        sap.runline(f'openquake.commands zip {ini} {xzip}')
        names = sorted(zipfile.ZipFile(xzip).namelist())
        self.assertEqual(['Wcrust_high_rhypo.hdf5',
                          'Wcrust_low_rhypo.hdf5',
                          'Wcrust_med_rhypo.hdf5',
                          'job.ini',
                          'nbc_asc_logic_tree.xml',
                          'point_source.xml',
                          'source_model_logic_tree.xml',
                          'vancouver_school_sites.csv'], names)
        shutil.rmtree(dtemp)

    def test_zip_gmf_ebrisk(self):
        # this is a case without gsims and with a gmf file
        ini = os.path.join(os.path.dirname(ebrisk.__file__), 'job_risk.ini')
        dtemp = tempfile.mkdtemp()
        xzip = os.path.join(dtemp, 'x.zip')
        sap.runline(f'openquake.commands zip {ini} {xzip}')
        names = sorted(zipfile.ZipFile(xzip).namelist())
        self.assertEqual(['exposure_model.xml', 'gmf_scenario.csv',
                          'job_risk.ini', 'sites.csv', 'vulnerability.xml'],
                         names)
        shutil.rmtree(dtemp)

    def test_zip_ebr(self):
        # this is a case with an exposure.csv
        ini = os.path.join(os.path.dirname(case_eb.__file__), 'job_ins.ini')
        dtemp = tempfile.mkdtemp()
        xzip = os.path.join(dtemp, 'x.zip')
        sap.runline(f'openquake.commands zip {ini} {xzip}')
        names = sorted(zipfile.ZipFile(xzip).namelist())
        self.assertEqual(
            ['exposure.csv', 'exposure1.xml', 'gmpe_logic_tree.xml',
             'job_ins.ini', 'policy_ins.csv', 'source_model.xml',
             'source_model_logic_tree.xml',
             'vulnerability_model_nonstco.xml',
             'vulnerability_model_stco.xml'],
            names)
        shutil.rmtree(dtemp)

    def test_zip_ssmLT(self):
        # zipping a directory containing a ssmLT.xml file
        dtemp = os.path.join(tempfile.mkdtemp(), 'inp')
        shutil.copytree(os.path.dirname(case_21.__file__), dtemp)
        sap.runline(f'openquake.commands zip {dtemp}')
        shutil.rmtree(dtemp)

    def test_shapefile(self):
        # zipping shapefiles used for ShakeMaps
        dtemp = os.path.join(tempfile.mkdtemp(), 'inp')
        shutil.copytree(os.path.dirname(case_shapefile.__file__), dtemp)
        sap.runline(f'openquake.commands zip {dtemp}/job.ini {dtemp}/job.zip')
        job_zip = os.path.join(dtemp, 'job.zip')
        names = sorted(zipfile.ZipFile(job_zip).namelist())
        self.assertIn('shp/output.dbf', names)
        self.assertIn('shp/output.prj', names)
        self.assertIn('shp/output.shp', names)
        self.assertIn('shp/output.shx', names)
        shutil.rmtree(dtemp)

    def test_shapefile_zipped(self):
        # zipping shapefile archive used for ShakeMaps
        dtemp = os.path.join(tempfile.mkdtemp(), 'inp')
        shutil.copytree(os.path.dirname(case_shapefile.__file__), dtemp)
        sap.runline(
            f'openquake.commands zip {dtemp}/job_zipped.ini {dtemp}/job.zip')
        job_zip = os.path.join(dtemp, 'job.zip')
        names = sorted(zipfile.ZipFile(job_zip).namelist())
        self.assertIn('shp/shapefiles.zip', names)
        shutil.rmtree(dtemp)

    def test_shakemap(self):
        # zipping *.npy shakemap with relative path for ShakeMaps
        dtemp = os.path.join(tempfile.mkdtemp(), 'inp')
        shutil.copytree(os.path.dirname(case_shakemap.__file__), dtemp)
        sap.runline(
            f'openquake.commands zip {dtemp}/job.ini {dtemp}/job.zip')
        job_zip = os.path.join(dtemp, 'job.zip')
        names = sorted(zipfile.ZipFile(job_zip).namelist())
        self.assertIn('shakefile/usp000fjta.npy', names)
        shutil.rmtree(dtemp)


class EngineRunJobTestCase(unittest.TestCase):
    def test_multi_run(self):
        job_ini = os.path.join(os.path.dirname(case_4.__file__), 'job.ini')
        jobs = create_jobs([job_ini, job_ini], 'error')
        run_jobs(jobs)
        with Print.patch():
            [r1, r2] = commonlib.logs.dbcmd(
                'select id, hazard_calculation_id from job '
                'where id in (?S) order by id', [job.calc_id for job in jobs])
        self.assertEqual(r1.hazard_calculation_id, None)
        self.assertEqual(r2.hazard_calculation_id, None)

    def test_OQ_REDUCE(self):
        with mock.patch.dict(os.environ, OQ_REDUCE='.1'):
            job_ini = os.path.join(os.path.dirname(case_4.__file__), 'job.ini')
            run_jobs(create_jobs([job_ini]))

    def test_sensitivity(self):
        # test the sensitivity of the UHS from the area_source_discretization
        job_ini = os.path.join(os.path.dirname(case_56.__file__), 'job.ini')
        sap.runline(f'openquake.commands engine --run {job_ini} -c 0')
        with Print.patch() as p:
            sap.runline('openquake.commands compare uhs -1 -2')
        print(p)
        self.assertIn('rms-diff', str(p))

    def test_ebr(self):
        # test a single case of `run_jobs`, but it is the most complex one,
        # event based risk with post processing
        job_ini = os.path.join(
            os.path.dirname(case_master.__file__), 'job.ini')
        with Print.patch() as p:
            [log] = run_jobs(create_jobs([job_ini], 'error'))
        self.assertIn('id | name', str(p))

        # check the exported outputs
        expected = set('''\
Aggregate Event Losses
Aggregate Loss Curves
Aggregate Loss Curves Statistics
Aggregate Losses
Aggregate Losses Statistics
Average Asset Losses
Average Asset Losses Statistics
Average Ground Motion Field
Earthquake Ruptures
Events
Full Report
Ground Motion Fields
Hazard Curves
Hazard Maps
Input Files
Realizations
Source Loss Table'''.splitlines())
        with Print.patch() as p:
            sap.runline(f'openquake.commands engine --lo {log.calc_id}')
        got = set(re.findall(r'\| ([\w ]+)', str(p))) - {'name'}
        if got != expected:
            print('Missing output', expected - got, file=sys.stderr)
        # sanity check on the performance views: make sure that the most
        # relevant information is stored (it can be lost due to a wrong
        # refactoring of the monitoring and it happened several times)
        with read(log.calc_id) as dstore:
            perf = str(view('performance', dstore))
            self.assertIn('total ebr_from_gmfs', perf)

    def test_oqdata(self):
        # the that the environment variable OQ_DATADIR is honored
        job_ini = os.path.join(os.path.dirname(case_15.__file__), 'job.ini')
        dic = get_params(job_ini)
        dic['calculation_mode'] = 'event_based'
        tempdir = tempfile.mkdtemp()
        with mock.patch.dict(os.environ, OQ_DATADIR=tempdir):
            [job] = run_jobs(create_jobs([dic], 'error'))
            job = commonlib.logs.dbcmd('get_job', job.calc_id)
            self.assertTrue(job.ds_calc_dir.startswith(tempdir),
                            job.ds_calc_dir)
        with Print.patch() as p:
            sap.runline(f'openquake.commands export ruptures {job.id} '
                        f'-e csv --export-dir={tempdir}')
        self.assertIn('Exported', str(p))

        # run the damage part; emulate using a different user for the hazard
        dic['calculation_mode'] = 'event_based_damage'
        run_jobs(create_jobs([dic], 'error', hc_id=job.id))
        shutil.rmtree(tempdir)

    def test_shakemap2gmfs(self):
        # test shakemap2gmfs with sitemodel with a filtered sitecol
        # and three choices of site_effects
        effects = ['no', 'shakemap', 'sitemodel']
        expected = [0.2555, 0.31813407, 0.25332582]
        with chdir(os.path.dirname(case_25.__file__)):
            for eff, exp in zip(effects, expected):
                with redirect_stdout(io.StringIO()) as out:
                    sap.runline('openquake.commands shakemap2gmfs usp0006dv8 '
                                'site_model_uniform_grid_rock.csv -n 1 -t 0 '
                                f'--spatialcorr no -c no --site-effects={eff}')
                got = out.getvalue()
                assert f'gmv_0={exp}' in got


class CheckInputTestCase(unittest.TestCase):
    def test_invalid(self):
        job_zip = os.path.join(list(test_data.__path__)[0],
                               'archive_err_1.zip')
        with self.assertRaises(ValueError):
            sap.runline(f'openquake.commands check_input {job_zip}')

    def test_valid(self):
        job_ini = os.path.join(list(test_data.__path__)[0],
                               'event_based_hazard/job.ini')
        sap.runline(f'openquake.commands check_input {job_ini}')


class PrepareSiteModelTestCase(unittest.TestCase):
    def test(self):
        inputdir = os.path.dirname(case_16.__file__)
        output = gettemp(suffix='.csv')
        grid_spacing = 50
        exposure_xml = os.path.join(inputdir, 'exposure.xml')
        vs30_csv = os.path.join(inputdir, 'vs30.csv.gz')
        sitecol = sap.runline('openquake.commands prepare_site_model '
                              f'-123 {vs30_csv} -e {exposure_xml} '
                              f'-g {grid_spacing} --assoc-distance=5 '
                              f'-o {output}')
        sm = read_csv(output, {None: float, 'vs30measured': numpy.uint8})
        self.assertEqual(sm['vs30measured'].sum(), 0)
        self.assertEqual(len(sitecol), 84)  # 84 non-empty grid points
        self.assertEqual(len(sitecol), len(sm))

        # test no grid
        sc = sap.runline('openquake.commands prepare_site_model '
                         f'{vs30_csv} -e {exposure_xml}')
        self.assertEqual(len(sc), 148)  # 148 sites within 5 km from the params

        # test sites_csv == vs30_csv and no grid
        sc = sap.runline('openquake.commands prepare_site_model '
                         f'{vs30_csv} -s{vs30_csv} -12 -a5 -o {output}')

        # test sites_csv == vs30_csv and grid spacing
        sc = sap.runline('openquake.commands prepare_site_model '
                         f'{vs30_csv} -s{vs30_csv} -12 -g10 -a5 -o {output}')


class ReduceSourceModelTestCase(unittest.TestCase):

    def test_reduce_sm_with_duplicate_source_ids(self):
        # testing reduce_sm in case of two sources with the same ID and
        # different codes (false duplicates)
        raise unittest.SkipTest(
            'reduce_sm does not work with false duplicates!')
        temp_dir = tempfile.mkdtemp()
        calc_dir = os.path.dirname(to_reduce.__file__)
        shutil.copytree(calc_dir, os.path.join(temp_dir, 'data'))
        job_ini = os.path.join(temp_dir, 'data', 'job.ini')
        with Print.patch():
            calc = sap.runline(f'openquake.commands run {job_ini}')
        calc_id = calc.datastore.calc_id
        with mock.patch('logging.info') as info:
            sap.runline(f'openquake.commands reduce_sm {calc_id}')
        self.assertIn('Removed %d/%d sources', info.call_args[0][0])
        shutil.rmtree(temp_dir)


class NRML2CSVTestCase(unittest.TestCase):

    def test_nrml_to_csv(self):
        temp_dir = tempfile.mkdtemp()
        with Print.patch() as p:
            sap.runline(f'openquake.commands nrml_to csv {MIXED_SRC_MODEL} '
                        f'--outdir={temp_dir} --chatty')
        out = str(p)
        self.assertIn('3D MultiPolygon', out)
        self.assertIn('3D MultiLineString', out)
        self.assertIn('Point', out)
        shutil.rmtree(temp_dir)


class NRML2GPKGTestCase(unittest.TestCase):

    def test_nrml_to_gpkg(self):
        temp_dir = tempfile.mkdtemp()
        with Print.patch() as p:
            sap.runline(f'openquake.commands nrml_to gpkg {MIXED_SRC_MODEL} '
                        f'--outdir={temp_dir} --chatty')
        out = str(p)
        self.assertIn('3D MultiPolygon', out)
        self.assertIn('3D MultiLineString', out)
        self.assertIn('Point', out)
        shutil.rmtree(temp_dir)


class GPKG2NRMLTestCase(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.datadir = os.path.join(os.path.dirname(__file__), 'data')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _convert_nrml_to_gpkg(self, source_model):
        with Print.patch():
            sap.runline(f'openquake.commands nrml_to gpkg {source_model} '
                        f'--outdir={self.temp_dir} --chatty')
        gpkg_path = os.path.join(
            self.temp_dir, Path(source_model).stem + '.gpkg')
        return gpkg_path

    def _convert_gpkg_to_nrml(self, gpkg_path, out_path):
        with Print.patch():
            sap.runline(f'openquake.commands nrml_from {gpkg_path} {out_path}')

    def _convert_nrml_to_gpkg_to_nrml(self, src_model_path):
        gpkg_path = self._convert_nrml_to_gpkg(src_model_path)
        out_path = os.path.join(
            self.temp_dir, Path(src_model_path).stem + '_converted.xml')
        self._convert_gpkg_to_nrml(gpkg_path, out_path)
        return out_path

    def _check_output(self, out_path, expected_path):
        self.assertListEqual(
            list(open(out_path)),
            list(open(expected_path)))

    def test_convert_mixed_nrml_from_gpkg(self):
        gpkg_path = self._convert_nrml_to_gpkg(MIXED_SRC_MODEL)
        out_path = os.path.join(
            self.temp_dir, Path(MIXED_SRC_MODEL).stem + '_converted.xml')
        expected_log_outputs = [
            'Skipping source of code "X" and attributes'
            ' "{\'id\': \'5\', \'name\': \'characteristic source,'
            ' simple fault\', \'tectonicRegion\': \'Volcanic\'}"'
            ' (the converter is not implemented yet)',
            'Skipping source of code "X" and attributes'
            ' "{\'id\': \'6\', \'name\': \'characteristic source,'
            ' complex fault\', \'tectonicRegion\': \'Volcanic\'}"'
            ' (the converter is not implemented yet)',
            'Skipping source of code "X" and attributes'
            ' "{\'id\': \'7\', \'name\': \'characteristic source,'
            ' multi surface\', \'tectonicRegion\': \'Volcanic\'}"'
            ' (the converter is not implemented yet)']
        with mock.patch('logging.error') as error:
            sap.runline(f'openquake.commands nrml_from {gpkg_path} {out_path}')
            errors = [error.call_args_list[i].args[0]
                      for i in range(len(error.call_args_list))]
            for line in expected_log_outputs:
                self.assertIn(line, errors)
        expected_path = os.path.join(
            self.datadir, 'expected_mixed_converted_nrml.xml')
        self._check_output(out_path, expected_path)

    def test_convert_AreaSource(self):
        out_path = self._convert_nrml_to_gpkg_to_nrml(AREA_SOURCE_SRC_MODEL)
        expected_path = os.path.join(
            self.datadir, 'expected_area_source_converted_nrml.xml')
        self._check_output(out_path, expected_path)

    def test_convert_ComplexFaultSource(self):
        out_path = self._convert_nrml_to_gpkg_to_nrml(COMPLEX_FAULT_SRC_MODEL)
        expected_path = os.path.join(
            self.datadir, 'expected_complex_fault_source_converted_nrml.xml')
        self._check_output(out_path, expected_path)

    def test_convert_MultiPointSource(self):
        out_path = self._convert_nrml_to_gpkg_to_nrml(MULTI_POINT_SRC_MODEL)
        expected_path = os.path.join(
            self.datadir, 'expected_multi_point_source_converted_nrml.xml')
        self._check_output(out_path, expected_path)

    def test_convert_PointSource(self):
        out_path = self._convert_nrml_to_gpkg_to_nrml(POINT_SRC_MODEL)
        expected_path = os.path.join(
            self.datadir, 'expected_point_source_converted_nrml.xml')
        self._check_output(out_path, expected_path)

    def test_convert_SimpleFaultSource(self):
        out_path = self._convert_nrml_to_gpkg_to_nrml(SIMPLE_FAULT_SRC_MODEL)
        expected_path = os.path.join(
            self.datadir, 'expected_simple_fault_source_converted_nrml.xml')
        self._check_output(out_path, expected_path)


def teardown_module():
    parallel.Starmap.shutdown()
    del os.environ['OQ_DATABASE']
