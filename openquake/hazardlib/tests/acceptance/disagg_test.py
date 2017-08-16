# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
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
import unittest
import codecs
import numpy

from openquake.hazardlib.source import AreaSource
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.scalerel import WC1994
from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008
from openquake.hazardlib.calc import disagg
from openquake.hazardlib.geo import Point, Polygon, NodalPlane
from openquake.hazardlib.mfd import TruncatedGRMFD
from openquake.hazardlib.imt import SA
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.site import Site


class DisaggTestCase(unittest.TestCase):
    def test_areasource(self):
        nodalplane = NodalPlane(strike=0.0, dip=90.0, rake=0.0)
        src = AreaSource(
            source_id='src_1',
            name='area source',
            tectonic_region_type='Active Shallow Crust',
            mfd=TruncatedGRMFD(a_val=3.5, b_val=1.0, min_mag=5.0,
                               max_mag=6.5, bin_width=0.1),
            nodal_plane_distribution=PMF([(1.0, nodalplane)]),
            hypocenter_distribution=PMF([(1.0, 5.0)]),
            upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=10.0,
            magnitude_scaling_relationship=WC1994(),
            rupture_aspect_ratio=1.0,
            polygon=Polygon([Point(-0.5, -0.5), Point(-0.5, 0.5),
                             Point(0.5, 0.5), Point(0.5, -0.5)]),
            area_discretization=9.0,
            rupture_mesh_spacing=1.0,
            temporal_occurrence_model=PoissonTOM(50.)
        )
        site = Site(location=Point(0.0, 0.0),
                    vs30=800.0,
                    vs30measured=True,
                    z1pt0=500.0,
                    z2pt5=2.0)
        gsims = {'Active Shallow Crust': BooreAtkinson2008()}
        imt = SA(period=0.1, damping=5.0)
        iml = 0.2
        truncation_level = 3.0
        n_epsilons = 3
        mag_bin_width = 0.2
        # in km
        dist_bin_width = 10.0
        # in decimal degree
        coord_bin_width = 0.2

        # compute disaggregation
        bin_edges, diss_matrix = disagg.disaggregation(
            [src], site, imt, iml, gsims, truncation_level,
            n_epsilons, mag_bin_width, dist_bin_width, coord_bin_width
        )
        mag_bins, dist_bins, lon_bins, lat_bins, eps_bins, trt_bins = bin_edges
        numpy.testing.assert_almost_equal(
            mag_bins, [5., 5.2, 5.4, 5.6, 5.8, 6., 6.2, 6.4, 6.6]
        )
        numpy.testing.assert_almost_equal(
            dist_bins, [0., 10., 20., 30., 40., 50., 60., 70., 80.]
        )
        numpy.testing.assert_almost_equal(
            lat_bins, [-0.6, -0.4, -0.2, 0., 0.2, 0.4, 0.6]
        )
        numpy.testing.assert_almost_equal(
            lon_bins, [-0.6, -0.4, -0.2, 0., 0.2, 0.4, 0.6]
        )
        numpy.testing.assert_almost_equal(
            eps_bins, [-3., -1., 1., 3.]
        )
        self.assertEqual(trt_bins, ['Active Shallow Crust'])

        expected_matrix = numpy.fromstring(codecs.decode(codecs.decode(b"""\
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\
""", 'base64'), 'zip')).reshape((8, 8, 6, 6, 3, 1))
        numpy.testing.assert_almost_equal(diss_matrix, expected_matrix)
