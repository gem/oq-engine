# The Hazard Library
# Copyright (C) 2014 GEM Foundation
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

import numpy

from openquake.hazardlib.source import AreaSource
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.scalerel import WC1994
from openquake.hazardlib.geo import Point, Polygon, NodalPlane
from openquake.hazardlib.mfd import TruncatedGRMFD
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.calc.stochastic import stochastic_event_set_poissonian


class StochasticEventSetTestCase(unittest.TestCase):

    def _extract_rates(self, ses, time_span, bins):
        """
        Extract annual rates of occurence from stochastic event set
        """
        mags = []
        for r in ses:
            mags.append(r.mag)

        rates = numpy.histogram(mags, bins=bins)
        rates = rates / time_span

        return rates

    def test_ses_generation_from_parametric_source(self):
        # generate stochastic event set (SES) from area source with given
        # magnitude frequency distribution (MFD). Check that the MFD as
        # obtained from the SES (by making an istogram of the magnitude values
        # and normalizing by the total duration of the catalog) is
        # approximately equal to the original MFD.
        nodalplane = NodalPlane(strike=0.0, dip=90.0, rake=0.0)
        mfd = TruncatedGRMFD(a_val=3.5, b_val=1.0, min_mag=5.0,
                             max_mag=6.5, bin_width=0.1)
        src = AreaSource(
            source_id='src_1',
            name='area source',
            tectonic_region_type='Active Shallow Crust',
            mfd=mfd,
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

        ses = stochastic_event_set_poissonian([src], time_span=50.)

        rates = self._extract_rates(ses, time_span=50.,
                                    bins=numpy.arange(5., 6.6, 0.1))

        expect_rates = numpy.array(
            [r for m, r in mfd.get_annual_occurrence_rates()]
        )

        numpy.testing.assert_allclose(rates, expect_rates)
