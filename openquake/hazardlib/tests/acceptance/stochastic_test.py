# The Hazard Library
# Copyright (C) 2014-2017 GEM Foundation
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
from openquake.hazardlib.geo import Point, NodalPlane
from openquake.hazardlib.mfd import TruncatedGRMFD
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.calc.stochastic import stochastic_event_set
from openquake.hazardlib.calc import filters
from openquake.hazardlib.site import Site, SiteCollection

from openquake.hazardlib.tests.source.non_parametric_test import \
    make_non_parametric_source


class StochasticEventSetTestCase(unittest.TestCase):

    def setUp(self):
        # time span of 10 million years
        self.time_span = 10e6

        nodalplane = NodalPlane(strike=0.0, dip=90.0, rake=0.0)
        self.mfd = TruncatedGRMFD(a_val=3.5, b_val=1.0, min_mag=5.0,
                                  max_mag=6.5, bin_width=0.1)

        # area source of circular shape with radius of 100 km
        # centered at 0., 0.
        self.area1 = AreaSource(
            source_id='src_1',
            name='area source',
            tectonic_region_type='Active Shallow Crust',
            mfd=self.mfd,
            nodal_plane_distribution=PMF([(1.0, nodalplane)]),
            hypocenter_distribution=PMF([(1.0, 5.0)]),
            upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=10.0,
            magnitude_scaling_relationship=WC1994(),
            rupture_aspect_ratio=1.0,
            polygon=Point(0., 0.).to_polygon(100.),
            area_discretization=9.0,
            rupture_mesh_spacing=1.0,
            temporal_occurrence_model=PoissonTOM(self.time_span)
        )

        # area source of circular shape with radius of 100 km
        # centered at 1., 1.
        self.area2 = AreaSource(
            source_id='src_1',
            name='area source',
            tectonic_region_type='Active Shallow Crust',
            mfd=self.mfd,
            nodal_plane_distribution=PMF([(1.0, nodalplane)]),
            hypocenter_distribution=PMF([(1.0, 5.0)]),
            upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=10.0,
            magnitude_scaling_relationship=WC1994(),
            rupture_aspect_ratio=1.0,
            polygon=Point(5., 5.).to_polygon(100.),
            area_discretization=9.0,
            rupture_mesh_spacing=1.0,
            temporal_occurrence_model=PoissonTOM(self.time_span)
        )

        # non-parametric source
        self.np_src, _ = make_non_parametric_source()

    def _extract_rates(self, ses, time_span, bins):
        """
        Extract annual rates of occurence from stochastic event set
        """
        mags = []
        for r in ses:
            mags.append(r.mag)

        rates, _ = numpy.histogram(mags, bins=bins)
        rates = rates / time_span

        return rates

    def test_ses_generation_from_parametric_source(self):
        # generate stochastic event set (SES) from area source with given
        # magnitude frequency distribution (MFD). Check that the MFD as
        # obtained from the SES (by making an histogram of the magnitude values
        # and normalizing by the total duration of the event set) is
        # approximately equal to the original MFD.
        numpy.random.seed(123)
        ses = stochastic_event_set([self.area1])

        rates = self._extract_rates(ses, time_span=self.time_span,
                                    bins=numpy.arange(5., 6.6, 0.1))

        expect_rates = numpy.array(
            [r for m, r in self.mfd.get_annual_occurrence_rates()]
        )

        numpy.testing.assert_allclose(rates, expect_rates, rtol=0, atol=1e-4)

    def test_ses_generation_from_parametric_source_with_filtering(self):
        # generate stochastic event set (SES) from 2 area sources (area1,
        # area2). However, by including a single site co-located with the
        # area1 center, and with source site filtering of 100 km (exactly
        # the radius of area1), the second source (area2), which is centered
        # at 5., 5. (that is about 500 km from center of area1), will be
        # excluded. the MFD from the SES will be therefore approximately equal
        # to the one of area1 only.
        numpy.random.seed(123)
        sites = SiteCollection([
            Site(
                location=Point(0., 0.), vs30=760, vs30measured=True,
                z1pt0=40., z2pt5=2.
            )
        ])
        ses = stochastic_event_set(
            [self.area1, self.area2],
            sites=sites,
            source_site_filter=filters.SourceFilter(sites, {'default': 100.})
        )

        rates = self._extract_rates(ses, time_span=self.time_span,
                                    bins=numpy.arange(5., 6.6, 0.1))

        expect_rates = numpy.array(
            [r for m, r in self.mfd.get_annual_occurrence_rates()]
        )

        numpy.testing.assert_allclose(rates, expect_rates, rtol=0, atol=1e-4)

    def test_ses_generation_from_non_parametric_source(self):
        # np_src contains two ruptures: rup1 (of magnitude 5) and rup2 (of
        # magnitude 6)
        # rup1 has probability of zero occurences of 0.7 and of one
        # occurrence of 0.3
        # rup2 has probability of zero occurrence of 0.7, of one occurrence of
        # 0.2 and of two occurrences of 0.1
        # the test generate multiple SESs. From the ensamble of SES the
        # probability of 0, 1, and 2, rupture occurrences is computed and
        # compared with the expected value
        numpy.random.seed(123)
        num_sess = 10000
        sess = [stochastic_event_set([self.np_src]) for i in range(num_sess)]

        # loop over ses. For each ses count number of rupture
        # occurrences (for each magnitude)
        n_rups1 = {}
        n_rups2 = {}
        for i, ses in enumerate(sess):
            n_rups1[i] = 0
            n_rups2[i] = 0
            for rup in ses:
                if rup.mag == 5.:
                    n_rups1[i] += 1
                if rup.mag == 6.:
                    n_rups2[i] += 1

        # count how many SESs have 0,1 or 2 occurrences, and then normalize
        # by the total number of SESs generated. This gives the probability
        # of having 0, 1 or 2 occurrences
        n_occs1 = numpy.array(list(n_rups1.values()))
        n_occs2 = numpy.array(list(n_rups2.values()))

        p_occs1_0 = float(len(n_occs1[n_occs1 == 0])) / num_sess
        p_occs1_1 = float(len(n_occs1[n_occs1 == 1])) / num_sess

        p_occs2_0 = float(len(n_occs2[n_occs2 == 0])) / num_sess
        p_occs2_1 = float(len(n_occs2[n_occs2 == 1])) / num_sess
        p_occs2_2 = float(len(n_occs2[n_occs2 == 2])) / num_sess

        self.assertAlmostEqual(p_occs1_0, 0.7, places=2)
        self.assertAlmostEqual(p_occs1_1, 0.3, places=2)
        self.assertAlmostEqual(p_occs2_0, 0.7, places=2)
        self.assertAlmostEqual(p_occs2_1, 0.2, places=2)
        self.assertAlmostEqual(p_occs2_2, 0.1, places=2)
