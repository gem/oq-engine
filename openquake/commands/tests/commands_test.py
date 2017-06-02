# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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
from __future__ import print_function
import os
import sys
import mock
import shutil
import tempfile
import unittest

from openquake.baselib.python3compat import encode
from openquake.baselib.general import writetmp
from openquake import commonlib
from openquake.commands.info import info
from openquake.commands.tidy import tidy
from openquake.commands.show import show
from openquake.commands.show_attrs import show_attrs
from openquake.commands.export import export
from openquake.commands.reduce import reduce
from openquake.commands.engine import run_job
from openquake.commands.db import db
from openquake.commands.to_shapefile import to_shapefile
from openquake.commands.from_shapefile import from_shapefile
from openquake.commands import run
from openquake.commands.upgrade_nrml import upgrade_nrml
from openquake.qa_tests_data.classical import case_1
from openquake.qa_tests_data.classical_risk import case_3
from openquake.qa_tests_data.scenario import case_4
from openquake.qa_tests_data.event_based import case_5
from openquake.qa_tests_data.event_based_risk import case_master
from openquake.server import manage, dbapi

DATADIR = os.path.join(commonlib.__path__[0], 'tests', 'data')


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
    EXPECTED = '''<CompositionInfo
b1, x15.xml, grp=[0], weight=1.00: 1 realization(s)>
See https://github.com/gem/oq-risklib/blob/master/doc/effective-realizations.rst for an explanation
<RlzsAssoc(size=1, rlzs=1)
0,AkkarBommer2010(): ['<0,b1~@_AkkarBommer2010_@_@_@_@_@,w=1.0>']>
=============== ======
attribute       nbytes
=============== ======'''

    def test_zip(self):
        path = os.path.join(DATADIR, 'frenchbug.zip')
        with Print.patch() as p:
            info(None, None, None, None, None, path)
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

    # NB: info --report is tested in the packager


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
            ruptureId="scenario-0"
            >
                
                <node gmv="1.26515E-02" lat="4.35812E+01" lon="1.21248E+01"/>
                <node gmv="1.24056E-02" lat="4.35812E+01" lon="1.21248E+01"/>
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
                      'float -0.012492 < 0, line 8', str(p))


class RunShowExportTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Build a datastore instance to show what it is inside
        """
        # the tests here gave mysterious core dumps in Ubuntu 16.04,
        # but only when called together with all other tests with the command
        # nosetests openquake/commonlib/
        job_ini = os.path.join(os.path.dirname(case_1.__file__), 'job.ini')
        with Print.patch() as cls.p:
            calc = run._run(job_ini, 0, False, 'info', None, '', {})
            calc.datastore.open()  # if closed
        cls.calc_id = calc.datastore.calc_id

    def test_run_calc(self):
        self.assertIn('See the output with hdfview', str(self.p))

    def test_show_calc(self):
        with Print.patch() as p:
            show('contents', self.calc_id)
        self.assertIn('sitecol', str(p))

        with Print.patch() as p:
            show('sitecol', self.calc_id)
        self.assertEqual(str(p), '<SiteCollection with 1 sites>')

        with Print.patch() as p:
            show('slow_sources', self.calc_id)
        self.assertIn('grp_id source_id source_class num_ruptures calc_time '
                      'num_sites num_split', str(p))

    def test_show_attrs(self):
        with Print.patch() as p:
            show_attrs('poes', self.calc_id)
        self.assertEqual('nbytes 48', str(p))

    def test_export_calc(self):
        tempdir = tempfile.mkdtemp()
        with Print.patch() as p:
            export('hcurves', self.calc_id, 'csv', tempdir)
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
        upgrade_nrml(tmpdir, False)
        shutil.rmtree(tmpdir)


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

    def test_roundtrip_valid(self):
        # test the conversion to shapefile and back for a valid file
        ssm = os.path.join(os.path.dirname(__file__),
                           "data", "sample_source_model.xml")
        to_shapefile(os.path.join(self.OUTDIR, 'smc'), ssm, True)
        shpfiles = [os.path.join(self.OUTDIR, f)
                    for f in os.listdir(self.OUTDIR)]
        from_shapefile(os.path.join(self.OUTDIR, 'smc'), shpfiles, True)


class DbTestCase(unittest.TestCase):
    def test_db(self):
        # the some db commands bypassing the dbserver
        with Print.patch(), mock.patch(
                'openquake.commonlib.logs.dbcmd', manage.dbcmd):
            db('version_db')
            try:
                db('calc_info', (1,))
            except dbapi.NotFound:  # happens on an empty db
                pass


class EngineRunJobTestCase(unittest.TestCase):
    """
    Test a single case of `run_job`, but it is the most complex one,
    event based risk with post processing
    """
    def test_ebr(self):
        job_ini = os.path.join(
            os.path.dirname(case_master.__file__), 'job.ini')
        with Print.patch() as p:
            run_job(job_ini, log_level='error')
        self.assertIn('id | name', str(p))
