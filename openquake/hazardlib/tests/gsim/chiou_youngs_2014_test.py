# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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

from openquake.hazardlib.gsim.chiou_youngs_2014 import (
    ChiouYoungs2014, ChiouYoungs2014PEER, ChiouYoungs2014NearFaultEffect)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.calc import ground_motion_fields
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGV
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.geo.surface import SimpleFaultSurface
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.point import Point


class ChiouYoungs2014TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChiouYoungs2014

    # Test data were obtained from a tool given by the authorst
    # in tests/gsim/data/NGA/CY14

    def test_mean_hanging_wall_normal_slip(self):
        self.check('NGA/CY14/CY14_MEDIAN_MS_HW_NM.csv',
                   max_discrep_percentage=0.05)

    def test_mean_hanging_wall_reversed_slip(self):
        self.check('NGA/CY14/CY14_MEDIAN_MS_HW_RV.csv',
                   max_discrep_percentage=0.05)

    def test_mean_hanging_wall_strike_slip(self):
        self.check('NGA/CY14/CY14_MEDIAN_MS_HW_SS.csv',
                   max_discrep_percentage=0.05)

    def test_inter_event_stddev(self):
        # data generated from opensha
        self.check('NGA/CY14/CY14_INTER_EVENT_SIGMA.csv',
                   max_discrep_percentage=0.05)

    def test_intra_event_stddev(self):
        # data generated from opensha
        self.check('NGA/CY14/CY14_INTRA_EVENT_SIGMA.csv',
                   max_discrep_percentage=0.05)

    def test_total_event_stddev(self):
        # data generated from opensha
        self.check('NGA/CY14/CY14_TOTAL_EVENT_SIGMA.csv',
                   max_discrep_percentage=0.05)


class ChiouYoungs2014PEERTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChiouYoungs2014PEER

    # First five tests use data ported from Kenneth Campbell
    # tables for verifying NGA models, available from OpenSHA, see
    # http://opensha.usc.edu/docs/opensha/NGA/Campbell_NGA_tests.zip
    # This data is distributed under different license, see LICENSE.txt
    # in tests/gsim/data/NGA
    def test_mean_hanging_wall_normal_slip(self):
        self.check('NGA/CY14/CY14_MEDIAN_MS_HW_NM.csv',
                   max_discrep_percentage=0.05)

    def test_mean_hanging_wall_reversed_slip(self):
        self.check('NGA/CY14/CY14_MEDIAN_MS_HW_RV.csv',
                   max_discrep_percentage=0.05)

    def test_mean_hanging_wall_strike_slip(self):
        self.check('NGA/CY14/CY14_MEDIAN_MS_HW_SS.csv',
                   max_discrep_percentage=0.05)

    def test_total_event_stddev(self):
        # Total Sigma fixes at 0.65
        self.check('NGA/CY14/CY14_TOTAL_EVENT_SIGMA_PEER.csv',
                   max_discrep_percentage=0.05)


class ChiouYoungs2014NearFaultTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChiouYoungs2014NearFaultEffect

    # First five tests use data ported from Kenneth Campbell
    # tables for verifying NGA models, available from OpenSHA, see
    # http://opensha.usc.edu/docs/opensha/NGA/Campbell_NGA_tests.zip
    # This data is distributed under different license, see LICENSE.txt
    # in tests/gsim/data/NGA

    def test_mean_near_fault(self):
        self.check('NGA/CY14/CY14_MEDIAN_RCDPP.csv',
                   max_discrep_percentage=0.05)


class ChiouYoungs2014NearFaultTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChiouYoungs2014NearFaultEffect

    # First five tests use data ported from Kenneth Campbell
    # tables for verifying NGA models, available from OpenSHA, see
    # http://opensha.usc.edu/docs/opensha/NGA/Campbell_NGA_tests.zip
    # This data is distributed under different license, see LICENSE.txt
    # in tests/gsim/data/NGA

    def test_mean_near_fault(self):
        self.check('NGA/CY14/CY14_MEDIAN_RCDPP.csv',
                   max_discrep_percentage=0.05)


class ChiouYoungs2014NearFaultDistanceTaperTestCase(BaseGSIMTestCase):

    def make_rupture(self):
        # Create the rupture surface.
        upper_seismogenic_depth = 3.
        lower_seismogenic_depth = 15.
        dip = 90.
        mesh_spacing = 1.

        fault_trace_start = Point(28.531397, 40.8790859336)
        fault_trace_end = Point(28.85, 40.9)
        fault_trace = Line([fault_trace_start, fault_trace_end])
        default_arguments = {
            'mag': 6.5,
            'rake': 180.,
            'tectonic_region_type': const.TRT.STABLE_CONTINENTAL,
            'hypocenter': Point(28.709146553353872, 40.890863701462457, 11.0),
            'surface': SimpleFaultSurface.from_fault_data(
                fault_trace, upper_seismogenic_depth, lower_seismogenic_depth,
                dip=dip, mesh_spacing=mesh_spacing),
            'source_typology': object(),
            'rupture_slip_direction': 0.,
            'occurrence_rate': 0.01,
            'temporal_occurrence_model': PoissonTOM(50)
        }
        kwargs = default_arguments
        rupture = ParametricProbabilisticRupture(**kwargs)
        return rupture

    def test_mearn_nearfault_distance_taper(self):

        rupture = self.make_rupture()
        site1 = Site(location=Point(27.9, 41), vs30=1200.,
                     vs30measured=True, z1pt0=2.36, z2pt5=2.)
        site2 = Site(location=Point(28.1, 41), vs30=1200.,
                     vs30measured=True, z1pt0=2.36, z2pt5=2.)
        sites = SiteCollection([site1, site2])

        fields = ground_motion_fields(
            rupture=rupture,
            sites=sites,
            imts=[PGV()],
            gsim=ChiouYoungs2014NearFaultEffect(),
            truncation_level=0,
            realizations=1.
        )
        gmf = fields[PGV()]
        self.assertAlmostEquals(2.27328758, gmf[0], delta=1e-4)
        self.assertAlmostEquals(3.38322998, gmf[1], delta=1e-4)
