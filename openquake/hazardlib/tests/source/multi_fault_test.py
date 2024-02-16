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
import cProfile
import tempfile
import unittest
import numpy
import pandas
import matplotlib.pyplot as plt
from openquake.baselib import hdf5, python3compat, general, writers
from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib import valid, contexts, calc
from openquake.hazardlib.source.multi_fault import (
    MultiFaultSource, build_secparams, save, load)
from openquake.hazardlib.geo.surface import KiteSurface
from openquake.hazardlib.tests.geo.surface import kite_fault_test as kst
from openquake.hazardlib.sourcewriter import write_source_model
from openquake.hazardlib.sourceconverter import SourceGroup
from openquake.hazardlib.nrml import SourceModel

BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
aac = numpy.testing.assert_allclose
PLOTTING = False


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

        # Sections
        sections = {0: sfc_a, 1: sfc_b, 2: sfc_c}

        # Rupture indexes
        rup_idxs = [numpy.uint16(x) for x in [[1, 2], [0], [1], [2],
                                              [0, 1], [0, 2], [0, 1, 2]]]

        # Magnitudes
        rup_mags = [5.8, 5.8, 5.8, 6.2, 6.2, 6.2, 6.5]
        rakes = [90.0, 90.0, 90.0, 90.0, 90.0, 90.0, 90.0]

        # Occurrence probabilities of occurrence
        pmfs = [[0.90, 0.10]] * 7
        self.sections = sections
        self.rup_idxs = rup_idxs
        self.pmfs = numpy.array(pmfs)
        self.mags = numpy.array(rup_mags)
        self.rakes = numpy.array(rakes)

    # NB: there are no flips in this test; see case_75 for that
    def test_ok(self):
        # test instantiation
        src = MultiFaultSource("01", "test", "Moon Crust",
                               self.pmfs, self.mags, self.rakes)
        src._rupture_idxs = self.rup_idxs
        src.mutex_weight = 1.

        # test conversion into XML
        src.sections = self.sections.values()
        smodel = SourceModel([SourceGroup("Moon Crust", [src], "test_group",
                                          src_interdep='mutex')])
        fd, tmp = tempfile.mkstemp(suffix='.xml')
        with os.fdopen(fd, 'wb'):
            sm_xml, gm_hdf5, gm_xml = write_source_model(tmp, smodel)

        # test save and load
        fname = general.gettemp(suffix='.hdf5')
        save([src], self.sections, fname)
        [got] = load(fname)
        for name in 'mags rakes probs_occur'.split():
            numpy.testing.assert_almost_equal(
                getattr(src, name), getattr(got, name))
        for a, b in zip(src.rupture_idxs, got.rupture_idxs):
            numpy.testing.assert_almost_equal(a, b)

        # check the stored section indices
        with hdf5.File(gm_hdf5, 'r') as f:
            lines = python3compat.decode(f['01/rupture_idxs'][:])
        self.assertEqual(lines, ['1 2', '0', '1', '2', '0 1', '0 2', '0 1 2'])

        # test rupture generation
        secparams = build_secparams(src.get_sections())
        src.set_msparams(secparams)
        rups = list(src.iter_ruptures())
        self.assertEqual(7, len(rups))

        # compute distances for the 7 underlying ruptures
        sitecol = SiteCollection.from_points([10.], [45.])
        sitecol._set('vs30', 760.)
        sitecol._set('vs30measured', 1)
        sitecol._set('z1pt0', 100.)
        sitecol._set('z2pt5', 5.)
        gsim = valid.gsim('AbrahamsonEtAl2014NSHMPMean')
        cmaker = contexts.simple_cmaker([gsim], ['PGA'])
        [ctx] = cmaker.from_srcs([src], sitecol)
        assert len(ctx) == src.count_ruptures()

        if PLOTTING:
            # plotting the 3 sections and then the multisurface
            # corresponding to the first rupture, with idxs=[1, 2];
            # the closest point to the site has longitude 10.35
            for sec in src.get_sections():
                lons = sec.mesh.lons
                lats = sec.mesh.lats
                plt.scatter(lons, lats, alpha=.1)
            plt.scatter(sitecol.lons, sitecol.lats, marker='+')
            mesh0 = rups[0].surface.mesh
            plt.scatter(mesh0.lons, mesh0.lats, marker='.')
            plt.scatter(ctx.clon[0], ctx.clat[0], marker='o')
            plt.show()

        # compare with the expected distances
        tol = 1e-4
        aac(ctx.rrup, [27.51933, 0., 27.51933, 55.03832,  0., 0., 0.], atol=tol)
        aac(ctx.rjb, [27.51907, 0., 27.51907, 55.03832,  0., 0., 0.], atol=tol)
        aac(ctx.rx, [1.653083e-01, 0, 1.102163e-01, 3.392963e-01, 1.686259e-05,
                     1.643886e-05, 3.3298e-05], atol=tol)
        aac(ctx.ry0, [27.5184749, 0., 27.518915, 55.03632, 0., 0., 0.],
            atol=tol)
        aac(ctx.clon, [10.35, 10., 10.35, 10.7, 10., 10., 10.])
        aac(ctx.clat, 45.)
            
    def test_ko(self):
        # test invalid section IDs
        rup_idxs = [[0], [1], [3], [0], [1], [3], [0]]
        mfs = MultiFaultSource("01", "test", "Moon Crust",
                               self.pmfs, self.mags, self.rakes)
        mfs._rupture_idxs = rup_idxs
        with self.assertRaises(IndexError) as ctx:
            save([mfs], self.sections, 'dummy.hdf5')
        self.assertEqual(str(ctx.exception),
                         "The section index 3 in source '01' is invalid")

    def test_slow(self):
        # performance test with a reduced UCERF source
        [src] = load(os.path.join(BASE_DATA_PATH, 'ucerf.hdf5'))
        sitecol = SiteCollection.from_points([-122, -121], [37, 27])
        sitecol._set('vs30', 760.)
        sitecol._set('vs30measured', 1)
        sitecol._set('z1pt0', 100.)
        sitecol._set('z2pt5', 5.)

        gsim = valid.gsim('AbrahamsonEtAl2014NSHMPMean')
        cmaker = contexts.simple_cmaker([gsim], ['PGA'])
        secparams = build_secparams(src.get_sections())
        src.set_msparams(secparams)
        [ctxt] = cmaker.from_srcs([src], sitecol)
        print(cmaker.ir_mon)
        print(cmaker.ctx_mon)

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
                    print('Look at col')
                    # breakpoint()


def main100sites():
    [src] = load(os.path.join(BASE_DATA_PATH, 'ucerf.hdf5'))
    lons = [-122.]
    lats = [27.]
    sitecol = SiteCollection.from_points(lons, lats)
    sitecol._set('vs30', 760.)
    sitecol._set('vs30measured', 1)
    sitecol._set('z1pt0', 100.)
    sitecol._set('z2pt5', 5.)
    gsim = valid.gsim('AbrahamsonEtAl2014NSHMPMean')
    cmaker = contexts.simple_cmaker([gsim], ['PGA'])
    secparams = build_secparams(src.get_sections())
    srcfilter = calc.filters.SourceFilter(sitecol, cmaker.maximum_distance)
    src.set_msparams(secparams)
    sites = srcfilter.get_close_sites(src)
    with cProfile.Profile() as prof:
        list(cmaker.get_ctx_iter(src, sites))
    prof.print_stats('cumulative')
    print(cmaker.ir_mon)
    print(cmaker.ctx_mon)
    # determine unique tors
    rups = list(src.iter_ruptures())
    lines = []
    data = []
    for rup in rups:
        for surf in rup.surface.surfaces:
            lines.append(surf.tor)
            data.append(surf.tor.coo.tobytes())
    uni, inv = numpy.unique(data, return_inverse=True)
    print('Found %d/%d unique segments' % (len(uni), len(data)))


if __name__ == '__main__':
    main100sites()
