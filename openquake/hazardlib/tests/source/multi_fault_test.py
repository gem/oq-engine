# The Hazard Library
# Copyright (C) 2021 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import tempfile
import unittest
import numpy
from openquake.baselib import hdf5, python3compat
from openquake.hazardlib.source.multi_fault import MultiFaultSource
from openquake.hazardlib.geo.surface import KiteSurface
from openquake.hazardlib.tests.geo.surface import kite_fault_test as kst
from openquake.hazardlib.sourcewriter import write_source_model
from openquake.hazardlib.sourceconverter import SourceGroup
from openquake.hazardlib.nrml import SourceModel

BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')


class MultiFaultTestCase(unittest.TestCase):
    """
    Test the construction of multi-fault ruptures
    """
    def setUp(self):

        hsmpl = 4
        vsmpl = 2
        idl = False
        alg = False

        # Create the surface of each section
        path = os.path.join(BASE_DATA_PATH, 'profiles00')
        prf, _ = kst._read_profiles(path)
        sfc_a = KiteSurface.from_profiles(prf, vsmpl, hsmpl, idl, alg)

        path = os.path.join(BASE_DATA_PATH, 'profiles01')
        prf, _ = kst._read_profiles(path)
        sfc_b = KiteSurface.from_profiles(prf, vsmpl, hsmpl, idl, alg)

        path = os.path.join(BASE_DATA_PATH, 'profiles02')
        prf, _ = kst._read_profiles(path)
        sfc_c = KiteSurface.from_profiles(prf, vsmpl, hsmpl, idl, alg)

        # Sections list
        sections = [sfc_a, sfc_b, sfc_c]

        # Rupture indexes
        rup_idxs = [[0], [1], [2], [0, 1], [0, 2],
                    [1, 2], [0, 1, 2]]

        # Magnitudes
        rup_mags = [5.8, 5.8, 5.8, 6.2, 6.2, 6.2, 6.5]
        rakes = [90.0, 90.0, 90.0, 90.0, 90.0, 90.0, 90.0]

        # Occurrence probabilities of occurrence
        pmfs = [[0.90, 0.10],
                [0.90, 0.10],
                [0.90, 0.10],
                [0.90, 0.10],
                [0.90, 0.10],
                [0.90, 0.10],
                [0.90, 0.10]]
        self.sections = sections
        self.rup_idxs = rup_idxs
        self.pmfs = pmfs
        self.mags = numpy.array(rup_mags)
        self.rakes = rakes

    def test01(self):
        # test instantiation
        src = MultiFaultSource("01", "test", "Moon Crust",
                               self.rup_idxs, self.pmfs, self.mags, self.rakes)
        src.set_sections(self.sections)
        src.mutex_weight = 1.

        # test conversion to XML
        smodel = SourceModel([SourceGroup("Moon Crust", [src], "test_group",
                                          src_interdep='mutex')])
        fd, tmp = tempfile.mkstemp(suffix='.xml')
        with os.fdopen(fd, 'wb'):
            sm_xml, gm_hdf5, gm_xml = write_source_model(tmp, smodel)
        # check the stored section indices
        with hdf5.File(gm_hdf5, 'r') as f:
            lines = python3compat.decode(f['01/rupture_idxs'][:])
        self.assertEqual(lines, ['0', '1', '2', '0 1', '0 2', '1 2', '0 1 2'])

        # test rupture generation
        rups = list(src.iter_ruptures())
        self.assertEqual(7, len(rups))

    def test02(self):
        # test set_sections, 3 is not a known section ID
        rup_idxs = [[0], [1], [3], [0], [1], [3], [0]]
        mfs = MultiFaultSource("01", "test", "Moon Crust", rup_idxs,
                               self.pmfs, self.mags, self.rakes)
        with self.assertRaises(IndexError) as ctx:
            mfs.set_sections(self.sections)
        expected = 'list index out of range'
        self.assertEqual(expected, str(ctx.exception))
