# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import copy
import numpy
import unittest
import pandas as pd

from openquake.hazardlib.geo import Point
from openquake.hazardlib.nrml import to_python
from openquake.hazardlib.contexts import ContextMaker
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.sourceconverter import SourceConverter
from openquake.hazardlib.gsim.abrahamson_2014 import AbrahamsonEtAl2014

from openquake.hazardlib.geo.surface.multi import _get_multi_line
from openquake.hazardlib.geo.multiline import get_tus

aac = numpy.testing.assert_allclose
aae = numpy.testing.assert_almost_equal

PLOTTING = False
BASE_PATH = os.path.dirname(__file__)


class GetRxRy0FromCacheTestCase(unittest.TestCase):
    """
    Tests the calculation of rx and ry0 with cache
    """

    def setUp(self):

        # Create site-collection
        path = os.path.join(BASE_PATH, 'data', 'multi_cache_01')
        fname = os.path.join(path, 'sites.csv')
        sites = pd.read_csv(fname, names=['lon', 'lat'])

        sites_list = []
        for i, row in sites.iterrows():
            site = Site(Point(row.lon, row.lat), vs30=760, z1pt0=30, z2pt5=0.5,
                        vs30measured=True)
            sites_list.append(site)
        self.sitec = SiteCollection(sites_list)

        # Create source
        rup_path = os.path.join(path, 'ruptures_26.xml')
        geom_path = os.path.join(path, 'ruptures_26_sections.xml')
        sc = SourceConverter(investigation_time=1, rupture_mesh_spacing=2.5)
        ssm = to_python(rup_path, sc)
        geom = to_python(geom_path, sc)
        sections = list(geom.sections.values())
        self.src = ssm[0][0]
        s2i = {suid: i for i, suid in enumerate(geom.sections)}
        self.src.rupture_idxs = [tuple(s2i[idx] for idx in idxs)
                                 for idxs in self.src.rupture_idxs]
        self.src.set_sections(sections)

    def test_multi_cache_01(self):
        """ Tests results remain stable after multiple calls """

        # Get rupture and top of ruptures
        rup = [r for r in self.src.iter_ruptures()][0]
        suids = [surf.suid for surf in rup.surface.surfaces]
        tors = rup.surface.tors
        tors._set_coordinate_shift()
        tors.set_tu(self.sitec.mesh)

        # Create the contexts
        gmm = AbrahamsonEtAl2014()
        param = dict(imtls={'PGA': []}, cache_distances=True)
        cm = ContextMaker('*', [gmm], param)
        [ctx] = cm.get_ctx_iter([rup], self.sitec)

        # Get the expected ry0 distance
        expected = tors.get_ry0_distance()
        aae(ctx.ry0, expected, decimal=3)

        # Test Ry0
        cache_save = copy.deepcopy(cm.dcache)
        [ctx] = cm.get_ctx_iter([rup], self.sitec)
        dcache = cm.dcache
        print('dcache.hit =', dcache.hit)

        # Get cached distances
        tupps = [dcache[i, 't_upp'] for i in suids]
        uupps = [dcache[i, 'u_upp'] for i in suids]
        weis = [dcache[i, 'wei'] for i in suids]
        umax = [dcache[i, 'umax'] for i in suids]
        lines = [dcache[key, 'tor'] for key in suids]

        # Expected distances
        e_tupps = [cache_save[i, 't_upp'] for i in suids]
        e_uupps = [cache_save[i, 'u_upp'] for i in suids]
        e_weis = [cache_save[i, 'wei'] for i in suids]
        e_umax = [cache_save[i, 'umax'] for i in suids]
        e_lines = [cache_save[key, 'tor'] for key in suids]

        # Check that data in the caches is the same
        aae(tupps, e_tupps, decimal=3)
        aae(uupps, e_uupps, decimal=3)
        aae(weis, e_weis, decimal=3)
        aae(umax, e_umax, decimal=3)
        for l1, l2 in zip(lines, e_lines):
            aae(l1.coo, l2.coo, decimal=3)

        # Check the attributes of the multiline
        ml1 = _get_multi_line(cache_save, suids)
        ml2 = _get_multi_line(dcache, suids)
        aae(ml1.u_max, ml2.u_max, decimal=3)
        aae(ml1.weis, ml2.weis, decimal=3)
        aae(ml1.shift, ml2.shift, decimal=3)
        aae(ml1.uupps, ml2.uupps, decimal=3)
        aae(ml1.tupps, ml2.tupps, decimal=3)

        # Check T and U
        ml1.set_tu()
        ml2.set_tu()
        #aae(ml1.uut, ml2.uut, decimal=3)
        #aae(ml1.tut, ml2.tut, decimal=3)

        # Check the recomputed ry0
        aae(ctx.ry0, expected, decimal=3)

    def test_multi_cache_02(self):
        # UCERF3 rupture

        rup = [r for r in self.src.iter_ruptures()][0]
        tors = rup.surface.tors
        tors._set_coordinate_shift()

        # Create the contexts
        gmm = AbrahamsonEtAl2014()
        param = dict(imtls={'PGA': []}, cache_distances=True)
        cm = ContextMaker('*', [gmm], param)
        ctxs = list(cm.get_ctx_iter(self.src, self.sitec))

        # Get multiline
        dcache = cm.dcache
        ml = _get_multi_line(dcache, self.src.rupture_idxs[0])

        # Test shift
        aae(tors.shift, ml.shift, decimal=4)

        # Test umax
        tors.set_u_max()
        aae(tors.u_max, ml.u_max, decimal=4)

        # Test uupps
        tupps, uupps, weis = get_tus(tors.lines, self.sitec.mesh)
        aae(tupps, ml.tupps, decimal=3)
        aae(uupps, ml.uupps, decimal=3)
        aae(weis, ml.weis, decimal=3)

        # Test T and U
        ml.set_tu(self.sitec.mesh)
        tors.set_tu(self.sitec.mesh)
        aae(ml.uut, ml.uut, decimal=3)
        aae(ml.tut, ml.tut, decimal=3)

        # Test Rx
        da = ml.get_rx_distance()
        expected = tors.get_rx_distance()
        aae(da, expected, decimal=3)

        # Test Ry0
        da = ml.get_ry0_distance()
        expected = tors.get_ry0_distance()
        aae(da, expected, decimal=3)
        aae(ctxs[0].ry0, expected, decimal=3)
