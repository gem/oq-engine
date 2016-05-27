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
from openquake.calculators.tests import check_platform
from openquake.commands.info import info
from openquake.commands.tidy import tidy
from openquake.commands.show import show
from openquake.commands.show_attrs import show_attrs
from openquake.commands.export import export
from openquake.commands.reduce import reduce
from openquake.commands import run
from openquake.qa_tests_data.classical import case_1
from openquake.qa_tests_data.classical_risk import case_3
from openquake.qa_tests_data.scenario import case_4
from openquake.qa_tests_data.event_based import case_5

DATADIR = os.path.join(os.path.dirname(__file__), 'data')


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
0,AkkarBommer2010(): ['<0,b1,@_AkkarBommer2010_@_@_@_@_@,w=1.0>']>
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
        self.assertIn('sitemesh', str(p))

        with Print.patch() as p:
            show('sitemesh', self.calc_id)
        self.assertEqual(str(p), '''\
lon,lat
0.000000E+00,0.000000E+00''')

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
