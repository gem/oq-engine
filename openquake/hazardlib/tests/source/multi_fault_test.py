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
import pandas
from openquake.baselib import hdf5, python3compat, general, performance, writers
from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib import valid, contexts
from openquake.hazardlib.source.multi_fault import (
    MultiFaultSource, save, load)
from openquake.hazardlib.geo.surface import KiteSurface
from openquake.hazardlib.tests.geo.surface import kite_fault_test as kst
from openquake.hazardlib.sourcewriter import write_source_model
from openquake.hazardlib.sourceconverter import SourceGroup
from openquake.hazardlib.nrml import SourceModel

BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
aac = numpy.testing.assert_allclose

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
        rup_idxs = [numpy.uint16(x) for x in [[0], [1], [2], [0, 1], [0, 2],
                                              [1, 2], [0, 1, 2]]]

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
        self.pmfs = numpy.array(pmfs)
        self.mags = numpy.array(rup_mags)
        self.rakes = numpy.array(rakes)

    def test_ok(self):
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

        # test save and load
        fname = general.gettemp(suffix='.hdf5')
        save([src], self.sections, fname)
        [got] = load(fname)
        for name in 'mags rakes probs_occur'.split():
            numpy.testing.assert_almost_equal(
                getattr(src, name), getattr(got, name))
        for a, b in zip(src.rupture_idxs, got.rupture_idxs):
            numpy.testing.assert_almost_equal(a, b)

        # test distances
        sitecol = SiteCollection.from_points([10.], [45.])
        gsim = valid.gsim('AbrahamsonEtAl2014NSHMPMean')
        cmaker = contexts.simple_cmaker([gsim], ['PGA'], cache_distances=1)
        [ctx] = cmaker.from_srcs([src], sitecol)
        aac(ctx.rrup, [0., 27.51929754, 55.03833836, 0., 0., 27.51929754,
                       0.])
        aac(ctx.rjb, [0., 27.51904144, 55.03833836, 0., 0., 27.51904144, 0.])
        aac(ctx.rx, [0, 1.10377738e-01, 3.39619736e-01, 1.68873152e-05,
                     1.64545240e-05, 1.65508566e-01, 3.33385038e-05])
        aac(ctx.ry0, [0., 27.519258, 55.038008, 0., 0., 27.518444, 0.])
        aac(ctx.clon, [10., 10.35, 10.7, 10., 10., 10.35, 10.])
        aac(ctx.clat, 45.)


    def test_ko(self):
        # test set_sections, 3 is not a known section ID
        rup_idxs = [[0], [1], [3], [0], [1], [3], [0]]
        mfs = MultiFaultSource("01", "test", "Moon Crust", rup_idxs,
                               self.pmfs, self.mags, self.rakes)
        with self.assertRaises(IndexError) as ctx:
            mfs.set_sections(self.sections)
        expected = 'list index out of range'
        self.assertEqual(expected, str(ctx.exception))


if __name__ == '__main__':
    # run a performance test with a reduced UCERF source
    srcs = load(os.path.join(BASE_DATA_PATH, 'ucerf.hdf5'))

    rups = list(srcs[0].iter_ruptures())
    lines = []
    data = []
    for rup in rups:
        for surf in rup.surface.surfaces:
            lines.append(surf.tor_line)
            data.append(surf.tor_line.coo.tobytes())
    uni, inv = numpy.unique(data, return_inverse=True)
    # only 230/174,486 lines are unique, i.e. a 760x speedup is possible
    print('Found %d/%d unique segments' % (len(uni), len(data)))

    sitecol = SiteCollection.from_points([-122], [37])  # San Francisco
    gsim = valid.gsim('AbrahamsonEtAl2014NSHMPMean')
    cmaker = contexts.simple_cmaker([gsim], ['PGA'], cache_distances=1)
    with performance.Monitor() as mon:
        [ctxt] = cmaker.from_srcs(srcs, sitecol)
    print(mon)
    dcache = srcs[0].dcache
    print(dcache)
    inp = os.path.join(BASE_DATA_PATH, 'ctxt.csv')
    out = os.path.join(BASE_DATA_PATH, 'ctxt-got.csv')
    ctx = ctxt[::50]
    if os.environ.get('OQ_OVERWRITE'):
        writers.write_csv(inp, ctx)
    else:
        writers.write_csv(out, ctx)
        df = pandas.read_csv(inp, na_values=['NAN'])
        aac = numpy.testing.assert_allclose
        for col in df.columns:
            if col == 'probs_occur:2':
                continue
            try:
                aac(df[col].to_numpy(), ctx[col], rtol=1E-5, equal_nan=1)
            except Exception:
                breakpoint()
