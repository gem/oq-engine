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

import os
import copy
import unittest
import tempfile
import toml
from openquake.baselib import general
from openquake.hazardlib.sourcewriter import write_source_model, tomldump
from openquake.hazardlib.sourceconverter import SourceConverter
from openquake.hazardlib import nrml

NONPARAM = os.path.join(os.path.dirname(__file__),
                        'source_model/nonparametric-source.xml')
NONPARAM_KITE = os.path.join(os.path.dirname(__file__),
                             'source_model/nonparametric-kite.xml')
MIXED = os.path.join(os.path.dirname(__file__),
                     'source_model/mixed.xml')
SLIP_RATE = os.path.join(os.path.dirname(__file__),
                         'source_model/complex-fault-source.xml')
ALT_MFDS = os.path.join(os.path.dirname(__file__),
                        'source_model/alternative-mfds_4test.xml')

COLLECTION = os.path.join(os.path.dirname(__file__),
                          'source_model/source_group_collection.xml')

# NB: this is RUP_MUTEX, SRC_MUTEX is tested in multi_fault_test
MUTEX = os.path.join(os.path.dirname(__file__),
                     'source_model/nonparametric-source-mutex-ruptures.xml')

MULTIPOINT = os.path.join(os.path.dirname(__file__),
                          'source_model/multi-point-source.xml')

MULTIFAULT = os.path.join(os.path.dirname(__file__),
                          'source_model/multi-fault-source.xml')

GRIDDED = os.path.join(os.path.dirname(__file__),
                       'source_model/gridded.xml')

KITEFAULT = os.path.join(os.path.dirname(__file__),
                         'source_model/kite-fault-source.xml')

TOML = os.path.join(os.path.dirname(__file__), 'expected_sources.toml')

conv = SourceConverter(50., 1., 20, 0.1, 10.)


class SourceWriterTestCase(unittest.TestCase):

    def check_round_trip(self, fname):
        smodel = nrml.to_python(fname, conv)
        fd, name = tempfile.mkstemp(suffix='.xml')
        with os.fdopen(fd, 'wb'):
            written = write_source_model(name, smodel)
        with open(name + '.toml', 'w') as f:
            tomldump(smodel, f)
        if len(written) == 2:  # .xml + .hdf5
            assert os.path.exists(written[1])
            os.remove(written[1])
        elif open(name).read() != open(fname).read():
            raise Exception('Different files: %s %s' % (name, fname))
        os.remove(name)
        os.remove(name + '.toml')
        return smodel

    def test_mixed(self):
        self.check_round_trip(MIXED)

    def test_nonparam_kite(self):
        self.check_round_trip(NONPARAM_KITE)

    def test_multi_fault(self):
        self.check_round_trip(MULTIFAULT)

    def test_kite_fault(self):
        self.check_round_trip(KITEFAULT)

    def test_nonparam(self):
        [[src]] = self.check_round_trip(NONPARAM)
        self.assertFalse(src.is_gridded())

    def test_gridded(self):
        self.check_round_trip(GRIDDED)

    def test_alt_mfds(self):
        self.check_round_trip(ALT_MFDS)

    def test_collection(self):
        self.check_round_trip(COLLECTION)

    def test_mutex(self):
        self.check_round_trip(MUTEX)

    def test_slip_rate(self):
        self.check_round_trip(SLIP_RATE)

    def test_multipoint(self):
        smodel = self.check_round_trip(MULTIPOINT)

        # test toml round trip
        temp = general.gettemp(suffix='.toml')
        with open(temp, 'w') as f:
            tomldump(smodel, f)
        with open(temp, 'r') as f:
            sm = toml.load(f)['sourceModel']
        self.assertEqual(smodel.name, sm['_name'])

    # NB: UCERF-like sources are tested in multi_fault_test.py


class TOMLTestCase(unittest.TestCase):
    def test_toml(self):
        out = ''
        for fname in (MIXED, ALT_MFDS, MULTIPOINT):
            smodel = nrml.to_python(fname, conv)
            for sgroup in smodel:
                for src in sgroup:
                    out += tomldump(src)
        # NB: uncomment the line below to regenerate the TOML file
        # with open(TOML, 'w') as f: f.write(out)
        self.assertEqual(out, open(TOML).read())


class DeepcopyTestCase(unittest.TestCase):
    def test_is_writeable(self):
        groups = [copy.deepcopy(grp)
                  for grp in nrml.to_python(ALT_MFDS, conv)]
        # there are a SimpleFaultSource and a CharacteristicFaultSource
        fd, fname = tempfile.mkstemp(suffix='.xml')
        with os.fdopen(fd, 'wb'):
            write_source_model(fname, groups, 'Test Source Model')
        # NB: without Node.__deepcopy__ the serialization would fail
        # with a RuntimeError: maximum recursion depth exceeded while
        # calling a Python object
