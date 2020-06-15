# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2020 GEM Foundation
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
import unittest.mock as mock
import shutil
import zipfile
import tempfile
import unittest
import numpy

from openquake.baselib.python3compat import encode
from openquake.baselib.general import gettemp
from openquake.baselib import parallel
from openquake.baselib.datastore import read
from openquake.baselib.hdf5 import read_csv
from openquake.hazardlib import tests
from openquake import commonlib
from openquake.commonlib.readinput import get_oqparam
from openquake.commands.info import info
from openquake.commands.tidy import tidy
from openquake.commands.show import show
from openquake.commands.show_attrs import show_attrs
from openquake.commands.export import export
from openquake.commands.extract import extract
from openquake.commands.sample import sample
from openquake.commands.reduce_sm import reduce_sm
from openquake.commands.engine import run_job, smart_run
from openquake.commands.db import db
from openquake.commands.to_shapefile import to_shapefile
from openquake.commands.from_shapefile import from_shapefile
from openquake.commands.zip import zip as zip_cmd
from openquake.commands.check_input import check_input
from openquake.commands.prepare_site_model import prepare_site_model
from openquake.commands.nrml_to import nrml_to, fiona
from openquake.commands import run
from openquake.commands.upgrade_nrml import upgrade_nrml
from openquake.commands.tests.data import to_reduce
from openquake.calculators.views import view
from openquake.qa_tests_data.classical import case_1, case_9, case_18
from openquake.qa_tests_data.classical_risk import case_3
from openquake.qa_tests_data.scenario import case_4
from openquake.qa_tests_data.event_based import (
    case_2, case_5, case_16, case_21)
from openquake.qa_tests_data.event_based_risk import (
    case_master, case_1 as case_eb)
from openquake.qa_tests_data.gmf_ebrisk import case_1 as ebrisk
from openquake.server import manage, dbapi, dbserver
from openquake.server.tests import data as test_data

DATADIR = os.path.join(commonlib.__path__[0], 'tests', 'data')
NRML_DIR = os.path.dirname(tests.__file__)
MIXED_SRC_MODEL = os.path.join(NRML_DIR, 'source_model/mixed.xml')


class Print(object):
    def __init__(self):
        self.lst = []

    def __call__(self, *args, **kw):
        self.lst.append(b' '.join(encode(str(a)) for a in args))

    def __str__(self):
        return b'\n'.join(self.lst).decode('utf-8')

    @classmethod
    def patch(cls):
        bprint = 'builtins.print' if sys.version > '3' else '__builtin__.print'
        return mock.patch(bprint, cls())


class InfoTestCase(unittest.TestCase):
    EXPECTED = '''<FullLogicTree
b1, x15.xml, weight=1.0: 1 realization(s)>
See http://docs.openquake.org/oq-engine/stable/effective-realizations.html for an explanation'''

    def test_zip(self):
        path = os.path.join(DATADIR, 'frenchbug.zip')
        with Print.patch() as p:
            info(path)
        self.assertEqual(self.EXPECTED, str(p)[:len(self.EXPECTED)])

    # poor man tests: checking that the flags produce a few characters
    # (more than 10) and do not break; I am not checking the precise output

    def test_calculators(self):
        with Print.patch() as p:
            info('calculators')
        self.assertGreater(len(str(p)), 10)

    def test_gsims(self):
        with Print.patch() as p:
            info('gsims')
        self.assertGreater(len(str(p)), 10)

    def test_imts(self):
        with Print.patch() as p:
            info('imts')
        self.assertGreaterEqual(len(str(p)), 18)

    def test_views(self):
        with Print.patch() as p:
            info('views')
        self.assertGreater(len(str(p)), 10)

    def test_exports(self):
        with Print.patch() as p:
            info('exports')
        self.assertGreater(len(str(p)), 10)

    def test_extracts(self):
        with Print.patch() as p:
            info('extracts')
        self.assertGreater(len(str(p)), 10)

    def test_parameters(self):
        with Print.patch() as p:
            info('parameters')
        self.assertGreater(len(str(p)), 10)

    def test_mfds(self):
        with Print.patch() as p:
            info('mfds')
        lines = str(p).split()
        self.assertGreaterEqual(len(lines), 5)

    def test_sources(self):
        with Print.patch() as p:
            info('sources')
        lines = str(p).split()
        self.assertGreaterEqual(len(lines), 10)

    def test_job_ini(self):
        path = os.path.join(os.path.dirname(case_9.__file__), 'job.ini')
        with Print.patch() as p:
            info(path)
        self.assertIn('<FullLogicTree\nb1_b2, source_model.xml, weight=0.5: 1 realization(s)\nb1_b3, source_model.xml, weight=0.5: 1 realization(s)>', str(p))

    def test_logictree(self):
        path = os.path.join(os.path.dirname(case_9.__file__),
                            'source_model_logic_tree.xml')
        with Print.patch() as p:
            info(path)
        self.assertEqual(str(p), """\
==================== ===========
TRT                  pointSource
==================== ===========
active shallow crust 1          
Total                1          
==================== ===========""")

    def test_report(self):
        path = os.path.join(os.path.dirname(case_9.__file__), 'job.ini')
        save = 'openquake.calculators.reportwriter.ReportWriter.save'
        with Print.patch() as p, mock.patch(save, lambda self, fname: None):
            info(path, True)
        self.assertIn('report.rst', str(p))

    def test_report_ebr(self):
        path = os.path.join(os.path.dirname(case_16.__file__), 'job.ini')
        save = 'openquake.calculators.reportwriter.ReportWriter.save'
        with Print.patch() as p, mock.patch(save, lambda self, fname: None):
            info(path, True)
        self.assertIn('report.rst', str(p))


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
            tidy([fname])
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
            tidy([fname])
        self.assertIn('Could not convert gmv->positivefloat: '
                      'float -0.012492 < 0, line 8', str(p))


class RunShowExportTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Build a datastore instance to show what it is inside
        """
        job_ini = os.path.join(os.path.dirname(case_1.__file__), 'job.ini')
        with Print.patch() as cls.p:
            calc = run._run([job_ini], 0, 'nojob', False, 'info', None, '', {})
        cls.calc_id = calc.datastore.calc_id

    def test_run_calc(self):
        self.assertIn('See the output with silx view', str(self.p))

    def test_show_calc(self):
        with Print.patch() as p:
            show('contents', self.calc_id)
        self.assertIn('sitecol', str(p))

        with Print.patch() as p:
            show('sitecol', self.calc_id)
        self.assertIn('sids,lon,lat,depth,vs30,vs30measured', str(p))

        with Print.patch() as p:
            show('slow_sources', self.calc_id)
        self.assertIn('source_id code multiplicity '
                      'calc_time num_sites', str(p))

    def test_show_attrs(self):
        with Print.patch() as p:
            show_attrs('sitecol', self.calc_id)
        self.assertEqual('__pyclass__ openquake.hazardlib.site.SiteCollection',
                         str(p))

    def test_show_oqparam(self):
        with Print.patch() as p:
            show('oqparam', self.calc_id)
        self.assertIn('"inputs": {', str(p))

    def test_export_calc(self):
        tempdir = tempfile.mkdtemp()
        with Print.patch() as p:
            export('hcurves', self.calc_id, 'csv', tempdir)
        fnames = os.listdir(tempdir)
        self.assertIn(str(fnames[0]), str(p))
        shutil.rmtree(tempdir)

    def test_extract_sitecol(self):
        tempdir = tempfile.mkdtemp()
        with Print.patch() as p:
            extract('sitecol', self.calc_id, extract_dir=tempdir)
        fnames = os.listdir(tempdir)
        self.assertIn(str(fnames[0]), str(p))
        shutil.rmtree(tempdir)


class SampleSmTestCase(unittest.TestCase):
    TESTDIR = os.path.dirname(case_3.__file__)

    def test_exposure(self):
        tempdir = tempfile.mkdtemp()
        dest = os.path.join(tempdir, 'exposure_model.xml')
        shutil.copy(os.path.join(self.TESTDIR, 'exposure_model.xml'), dest)
        with Print.patch() as p:
            sample(dest, 0.5)
        self.assertIn('Extracted 8 nodes out of 13', str(p))
        shutil.rmtree(tempdir)

    def test_source_model(self):
        tempdir = tempfile.mkdtemp()
        dest = os.path.join(tempdir, 'source_model.xml')
        shutil.copy(os.path.join(self.TESTDIR, 'source_model.xml'), tempdir)
        with Print.patch() as p:
            sample(dest, 0.5)
        self.assertIn('Extracted 9 nodes out of 15', str(p))
        shutil.rmtree(tempdir)

    def test_site_model(self):
        testdir = os.path.dirname(case_4.__file__)
        tempdir = tempfile.mkdtemp()
        dest = os.path.join(tempdir, 'site_model.xml')
        shutil.copy(os.path.join(testdir, 'site_model.xml'), tempdir)
        with Print.patch() as p:
            sample(dest, 0.5)
        self.assertIn('Extracted 2 nodes out of 3', str(p))
        shutil.rmtree(tempdir)

    def test_sites_csv(self):
        testdir = os.path.dirname(case_5.__file__)
        tempdir = tempfile.mkdtemp()
        dest = os.path.join(tempdir, 'sites.csv')
        shutil.copy(os.path.join(testdir, 'sites.csv'), tempdir)
        with Print.patch() as p:
            sample(dest, 0.5)
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
        upgrade_nrml(tmpdir, False, False)
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
        zip_cmd(ini, xzip, None)
        names = sorted(zipfile.ZipFile(xzip).namelist())
        self.assertEqual(['Wcrust_high_rhypo.hdf5',
                          'Wcrust_low_rhypo.hdf5',
                          'Wcrust_med_rhypo.hdf5',
                          'job.ini',
                          'nbc_asc_logic_tree.xml',
                          'source_model_logic_tree.xml',
                          'vancouver_area_source.xml',
                          'vancouver_school_sites.csv'], names)
        shutil.rmtree(dtemp)

    def test_zip_gmf_ebrisk(self):
        # this is a case without gsims and with a gmf file
        ini = os.path.join(os.path.dirname(ebrisk.__file__), 'job_risk.ini')
        dtemp = tempfile.mkdtemp()
        xzip = os.path.join(dtemp, 'x.zip')
        zip_cmd(ini, xzip, None)
        names = sorted(zipfile.ZipFile(xzip).namelist())
        self.assertEqual(['exposure_model.xml', 'gmf_scenario.csv',
                          'job_risk.ini', 'sites.csv', 'vulnerability.xml'],
                         names)
        shutil.rmtree(dtemp)

    def test_zip_ebr(self):
        # this is a case with an exposure.csv
        ini = os.path.join(os.path.dirname(case_eb.__file__), 'job_eb.ini')
        dtemp = tempfile.mkdtemp()
        xzip = os.path.join(dtemp, 'x.zip')
        zip_cmd(ini, xzip, None)
        names = sorted(zipfile.ZipFile(xzip).namelist())
        self.assertEqual(
            ['exposure.csv', 'exposure1.xml', 'gmpe_logic_tree.xml',
             'job_eb.ini', 'policy.csv', 'source_model.xml',
             'source_model_logic_tree.xml',
             'vulnerability_model_nonstco.xml',
             'vulnerability_model_stco.xml'],
            names)
        shutil.rmtree(dtemp)

    def test_zip_ssmLT(self):
        # zipping a directory containing a ssmLT.xml file
        dtemp = os.path.join(tempfile.mkdtemp(), 'inp')
        shutil.copytree(os.path.dirname(case_21.__file__), dtemp)
        zip_cmd(dtemp)
        shutil.rmtree(dtemp)


class SourceModelShapefileConverterTestCase(unittest.TestCase):
    """
    Simple conversion test for the Source Model to shapefile converter
    - more tests will follow
    """
    def setUp(self):
        self.OUTDIR = tempfile.mkdtemp()

    def test_roundtrip_invalid(self):
        # test the conversion to shapefile and back for an invalid file
        smc = os.path.join(os.path.dirname(__file__),
                           "data", "source_model_complete.xml")
        to_shapefile(os.path.join(self.OUTDIR, 'smc'), smc, False)
        shpfiles = [os.path.join(self.OUTDIR, f)
                    for f in os.listdir(self.OUTDIR)]
        from_shapefile(os.path.join(self.OUTDIR, 'smc'), shpfiles, False)

        # test invalid file
        with self.assertRaises(Exception) as ctx:
            to_shapefile(os.path.join(self.OUTDIR, 'smc'), smc, True)
        self.assertIn('Edges points are not in the right order',
                      str(ctx.exception))

    def test_roundtrip_valid_04(self):
        # test the conversion to shapefile and back for a valid file NRML 0.4
        ssm = os.path.join(os.path.dirname(__file__),
                           "data", "sample_source_model.xml")
        to_shapefile(os.path.join(self.OUTDIR, 'smc'), ssm, True)
        shpfiles = [os.path.join(self.OUTDIR, f)
                    for f in os.listdir(self.OUTDIR)]
        from_shapefile(os.path.join(self.OUTDIR, 'smc'), shpfiles, True)

    def test_roundtrip_valid_05(self):
        # test the conversion to shapefile and back for a valid file NRML 0.5
        ssm = os.path.join(os.path.dirname(__file__),
                           "data", "sample_source_model_05.xml")
        to_shapefile(os.path.join(self.OUTDIR, 'smc'), ssm, True)
        shpfiles = [os.path.join(self.OUTDIR, f)
                    for f in os.listdir(self.OUTDIR)]
        from_shapefile(os.path.join(self.OUTDIR, 'smc'), shpfiles, True)

    def tearDown(self):
        # comment out the line below if you need to debug the test
        shutil.rmtree(self.OUTDIR)


class DbTestCase(unittest.TestCase):
    def test_db(self):
        # the some db commands bypassing the dbserver
        with Print.patch(), mock.patch(
                'openquake.commonlib.logs.dbcmd', manage.fakedbcmd):
            db('db_version')
            try:
                db('calc_info', (1,))
            except dbapi.NotFound:  # happens on an empty db
                pass


class EngineRunJobTestCase(unittest.TestCase):
    def test_ebr(self):
        # test a single case of `run_job`, but it is the most complex one,
        # event based risk with post processing
        job_ini = os.path.join(
            os.path.dirname(case_master.__file__), 'job.ini')
        with Print.patch() as p:
            job_id = run_job(job_ini, log_level='error')
        self.assertIn('id | name', str(p))

        # sanity check on the performance views: make sure that the most
        # relevant information is stored (it can be lost due to a wrong
        # refactoring of the monitoring and it happened several times)
        with read(job_id) as dstore:
            perf = view('performance', dstore)
            self.assertIn('total event_based_risk', perf)

    def test_smart_run(self):
        # test smart_run with gmf_ebrisk, since it was breaking
        ini = os.path.join(os.path.dirname(ebrisk.__file__), 'job_risk.ini')
        oqparam = get_oqparam(ini)
        smart_run(ini, oqparam, 'info', None, '', False)

    def test_oqdata(self):
        # the that the environment variable OQ_DATADIR is honored
        job_ini = os.path.join(os.path.dirname(case_2.__file__), 'job_2.ini')
        tempdir = tempfile.mkdtemp()
        dbserver.ensure_on()
        with mock.patch.dict(os.environ, OQ_DATADIR=tempdir):
            job_id = run_job(job_ini, log_level='error')
            job = commonlib.logs.dbcmd('get_job', job_id)
            self.assertTrue(job.ds_calc_dir.startswith(tempdir),
                            job.ds_calc_dir)
        with Print.patch() as p:
            export('ruptures', job_id, 'csv', tempdir)
        self.assertIn('Exported', str(p))
        shutil.rmtree(tempdir)


class CheckInputTestCase(unittest.TestCase):
    def test_invalid(self):
        job_zip = os.path.join(list(test_data.__path__)[0],
                               'archive_err_1.zip')
        with self.assertRaises(ValueError):
            check_input([job_zip])

    def test_valid(self):
        job_ini = os.path.join(list(test_data.__path__)[0],
                               'event_based_hazard/job.ini')
        check_input([job_ini])


class PrepareSiteModelTestCase(unittest.TestCase):
    def test(self):
        inputdir = os.path.dirname(case_16.__file__)
        output = gettemp(suffix='.csv')
        grid_spacing = 50
        exposure_xml = os.path.join(inputdir, 'exposure.xml')
        vs30_csv = os.path.join(inputdir, 'vs30.csv')
        sitecol = prepare_site_model(
            [exposure_xml], [], [vs30_csv], True, True, True,
            grid_spacing, 5, output)
        sm = read_csv(output, {None: float, 'vs30measured': numpy.uint8})
        self.assertEqual(sm['vs30measured'].sum(), 0)
        self.assertEqual(len(sitecol), 84)  # 84 non-empty grid points
        self.assertEqual(len(sitecol), len(sm))

        # test no grid
        sc = prepare_site_model([exposure_xml], [], [vs30_csv],
                                True, True, False, 0, 5, output)
        self.assertEqual(len(sc), 148)  # 148 sites within 5 km from the params

        # test sites_csv
        sc = prepare_site_model([], [output], [vs30_csv],
                                True, True, False, 0, 5, output)


class ReduceSourceModelTestCase(unittest.TestCase):

    def test_reduce_sm_with_duplicate_source_ids(self):
        # testing reduce_sm in case of two sources with the same ID and
        # different codes
        temp_dir = tempfile.mkdtemp()
        calc_dir = os.path.dirname(to_reduce.__file__)
        shutil.copytree(calc_dir, os.path.join(temp_dir, 'data'))
        job_ini = os.path.join(temp_dir, 'data', 'job.ini')
        with Print.patch():
            calc = run._run([job_ini], 0, 'nojob', False, 'info', None, '', {})
        calc_id = calc.datastore.calc_id
        with mock.patch('logging.info') as info:
            reduce_sm(calc_id)
        self.assertIn('there are duplicated source IDs', info.call_args[0][0])
        shutil.rmtree(temp_dir)


class NRML2CSVTestCase(unittest.TestCase):

    def test_nrml_to_csv(self):
        temp_dir = tempfile.mkdtemp()
        with Print.patch() as p:
            nrml_to.func('csv', [MIXED_SRC_MODEL], temp_dir, chatty=True)
        out = str(p)
        self.assertIn('3D MultiPolygon', out)
        self.assertIn('3D MultiLineString', out)
        self.assertIn('Point', out)
        shutil.rmtree(temp_dir)

    def test_nrml_to_gpkg(self):
        if not fiona:
            raise unittest.SkipTest('fiona is missing')
        temp_dir = tempfile.mkdtemp()
        with Print.patch() as p:
            nrml_to.func('gpkg', [MIXED_SRC_MODEL], temp_dir, chatty=True)
        out = str(p)
        self.assertIn('3D MultiPolygon', out)
        self.assertIn('3D MultiLineString', out)
        self.assertIn('Point', out)
        shutil.rmtree(temp_dir)


def teardown_module():
    parallel.Starmap.shutdown()
