# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
import numpy as np
import copy
from openquake.hazardlib.gsim.chiou_youngs_2014 import (
    ChiouYoungs2014, ChiouYoungs2014PEER, ChiouYoungs2014NearFaultEffect,
    ChiouYoungs2014Japan, ChiouYoungs2014Italy, ChiouYoungs2014Wenchuan)

from openquake.hazardlib.gsim.chiou_youngs_2014 import (
    _get_delta_cm, get_magnitude_scaling, _get_delta_g)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.calc.gmf import ground_motion_fields
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGV, from_string
from openquake.hazardlib.contexts import ContextMaker
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.geo.surface import SimpleFaultSurface
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.point import Point

path_adj_table = os.path.join(os.path.dirname(__file__),
                              '..', '..', 'gsim', 'chiou_youngs_2014',
                              'path_adjustment_table_target_region_idaho.txt')


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

    def test_mean_refactor(self):
        # Test for backward compatibility - and extended test table
        self.check('NGA/CY14/cy14_extended_table_mean.csv',
                   max_discrep_percentage=0.001)

    def test_total_stddev_refactor(self):
        # Test for backward compatibility - and extended test table
        self.check('NGA/CY14/cy14_extended_table_total_stddev.csv',
                   max_discrep_percentage=0.001)


# Note that in the regionalisation cases the discrepancy percentage is raised
# to 1 % to allow for a different interpretation of the deltaZ1.0 when Z1.0 = 0
# when compared to the verification code
class ChiouYoungs2014JapanTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChiouYoungs2014Japan

    def test_mean_japan(self):
        # Data generated from implementation from Yue Hua
        # https://web.stanford.edu/~bakerjw/GMPEs/CY_2014_nga.m
        self.check('NGA/CY14/CY14_Japan_MEAN.csv',
                   max_discrep_percentage=1.0)


class ChiouYoungs2014ItalyTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChiouYoungs2014Italy

    def test_mean_italy(self):
        # Data generated from implementation from Yue Hua
        # https://web.stanford.edu/~bakerjw/GMPEs/CY_2014_nga.m
        self.check('NGA/CY14/CY14_Italy_MEAN.csv',
                   max_discrep_percentage=1.0)


class ChiouYoungs2014WenchuanTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChiouYoungs2014Wenchuan

    def test_mean_wenchuan(self):
        # Data generated from implementation from Yue Hua
        # https://web.stanford.edu/~bakerjw/GMPEs/CY_2014_nga.m
        self.check('NGA/CY14/CY14_Wenchuan_MEAN.csv',
                   max_discrep_percentage=1.0)


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


def _make_rupture():
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
        'rupture_slip_direction': 0.,
        'occurrence_rate': 0.01,
        'temporal_occurrence_model': PoissonTOM(50)
    }
    kwargs = default_arguments
    rupture = ParametricProbabilisticRupture(**kwargs)
    return rupture


class ChiouYoungs2014NearFaultDistanceTaperTestCase(BaseGSIMTestCase):

    def test_mean_nearfault_distance_taper(self):
        rupture = _make_rupture()
        site1 = Site(location=Point(27.9, 41), vs30=1200.,
                     vs30measured=True, z1pt0=2.36, z2pt5=2.)
        site2 = Site(location=Point(28.1, 41), vs30=1200.,
                     vs30measured=True, z1pt0=2.36, z2pt5=2.)
        sites = SiteCollection([site1, site2])

        fields = ground_motion_fields(
            rupture, sites, [PGV()], ChiouYoungs2014NearFaultEffect(),
            truncation_level=0, realizations=1)
        gmf = fields[PGV()]
        np.testing.assert_allclose(gmf, [[2.2739506], [3.3840923]])


class BooreEtAl2022Adjustments(BaseGSIMTestCase):
    """
    Test the adjustments to CY14 as proposed in Boore et al. (2022).
    """
    def test_stress_and_path_adjustments(self):
        """
        Test the stress adjustment and the path adjustment terms as described
        within Boore et al. (2022). The path adjustment table is taken from
        table 2 of the paper, which uses Idaho as the target region - we take
        the central branch (branch 3) values for use in these unit tests.
        """
        # Create GMMs
        gmm_ori = ChiouYoungs2014()
        gmm_adj_src = ChiouYoungs2014(stress_par_host=100,
                                      stress_par_target=120)
        gmm_adj_all = ChiouYoungs2014(stress_par_host=100,
                                      stress_par_target=120,
                                      delta_gamma_tab=path_adj_table)

        # Settings
        imt_str = 'SA(0.1)'
        imt = from_string('SA(0.1)')
        rupa = _make_rupture()
        rupb = copy.copy(rupa)
        rups = [rupa, rupb]
        site1 = Site(location=Point(27.9, 41), vs30=1200., vs30measured=True,
                     z1pt0=25.0, z2pt5=1.)
        mags_str = [f'{r.mag:.2f}' for r in rups]
        oqp = {'imtls': {k: [] for k in [imt_str]}, 'mags': mags_str}

        # ContextMaker for the ORIGINAL version of CY14
        ctxm_ori = ContextMaker('fake', [gmm_ori], oqp)
        ctxs_ori = list(ctxm_ori.get_ctx_iter(rups, SiteCollection([site1])))
        ctxs_ori = ctxs_ori[0]

        # ContextMaker for the SOURCE ADJUSTED version of CY14
        ctxm_adj_src = ContextMaker('fake', [gmm_adj_src], oqp)
        ctxs_adj_src = list(ctxm_adj_src.get_ctx_iter(rups,
                                                      SiteCollection([site1])))
        ctxs_adj_src = ctxs_adj_src[0]

        # ContextMaker for the SOURCE AND PATH ADJUSTED version of CY14
        ctxm_adj_all = ContextMaker('fake', [gmm_adj_all], oqp)
        ctxs_adj_all = list(ctxm_adj_all.get_ctx_iter(rups,
                                                      SiteCollection([site1])))
        ctxs_adj_all = ctxs_adj_all[0]

        # Compute mean values of ground motion
        [_, _, _, _] = ctxm_ori.get_mean_stds([ctxs_ori])
        [mea_adj_src, _, _, _] = ctxm_adj_src.get_mean_stds([ctxs_adj_src])
        [mea_adj_all, _, _, _] = ctxm_adj_all.get_mean_stds([ctxs_adj_all])

        # Check mean adjusted values are as expected
        expected_adj_src = -2.5796011
        expected_adj_all = -2.935969
        self.assertAlmostEqual(mea_adj_src[0][0][0], expected_adj_src)
        self.assertAlmostEqual(mea_adj_all[0][0][0], expected_adj_all)

        # Test delta_cm term
        delta_cm = _get_delta_cm(gmm_adj_all.conf, imt)
        expected_delta_cm = 0.149652555  # From hand-made calc
        msg = f"The value of the computed delta_cm {delta_cm} is different \n"
        msg += f"than the expected one {expected_delta_cm}"
        self.assertAlmostEqual(delta_cm, expected_delta_cm, msg=msg)

        # Test stress scaling term
        C = gmm_ori.COEFFS[imt]
        scalf_adj = get_magnitude_scaling(C, ctxs_adj_all[0].mag, delta_cm)
        expected_scalf_adj = np.array([0.665226, 0.665226])
        msg = f"The value of the scaling factor {scalf_adj} is different \n"
        msg += f"than the expected one {expected_scalf_adj}"
        np.testing.assert_almost_equal(
            scalf_adj, expected_scalf_adj, err_msg=msg)

        # Test delta_g term
        path_adj = _get_delta_g(gmm_adj_all.conf['delta_gamma_tab'],
                                ctxs_adj_all, imt)
        # Value is obtained from central branch (branch 3) of table 2 for
        # SA(0.1) when using eq 13
        expected_path_adj = np.array([-0.0065052, -0.0065052])
        msg = f"The value of the path adjustment {path_adj} is different \n"
        msg += f"than the expected one {expected_path_adj}"
        np.testing.assert_almost_equal(
            path_adj, expected_path_adj, err_msg=msg)
