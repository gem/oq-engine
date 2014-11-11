# Copyright (c) 2010-2014, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


import os
import getpass
import unittest
import mock
import numpy

from nose.plugins.attrib import attr

from openquake.hazardlib.imt import PGA
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.surface.complex_fault import ComplexFaultSurface
from openquake.hazardlib.gsim import get_available_gsims

from openquake.engine.db import models
from openquake.engine.calculators.hazard.event_based import core

from openquake.engine.tests.calculators.hazard.event_based \
    import _pp_test_data as test_data
from openquake.engine.tests.utils import helpers


def make_site_coll(lon, lat, n):
    assert n <= 1000
    sites = []
    for i in range(n):
        site = Site(Point(lon - float(i) / 1000, lat),
                    800., 'measured', 50., 2.5, i)
        sites.append(site)
    return SiteCollection(sites)


class FakeRupture(object):
    def __init__(self, id, trt, mag=5.0, rake=90.):
        self.hypocenter = Point(17.788328, -77.219496, 7.8125)
        lons = numpy.array(
            [-78.18106621, -78.18013243, -78.17919864, -78.15399318,
             -78.15305962, -78.15212606])
        lats = numpy.array(
            [15.615, 15.615, 15.615, 15.56553731,
             15.56553731,  15.56553731])
        self.surface = ComplexFaultSurface(Mesh(lons, lats, None))
        self.mag = mag
        self.rake = rake
        self.id = id
        self.site_indices = None


class GmfCalculatorTestCase(unittest.TestCase):
    """Tests for the routines used by the event-based hazard calculator"""

    # test a case with 5 sites and 2 ruptures
    def test_compute_gmf(self):
        hc = mock.Mock()
        hc.ground_motion_correlation_model = None
        hc.truncation_level = None
        hc.maximum_distance = 200.

        trt = 'Subduction Interface'
        gsim = get_available_gsims()['AkkarBommer2010']()
        num_sites = 5
        site_coll = make_site_coll(-78, 15.5, num_sites)
        rup_id, rup_seed = 42, 44
        rup = FakeRupture(rup_id, trt)
        pga = PGA()
        rlz = mock.Mock()
        rlz.id = 1
        calc = core.GmfCalculator(
            [pga], [gsim], trt_model_id=1, truncation_level=3)
        calc.calc_gmfs(site_coll, rup, [(rup.id, rup_seed)])
        expected_rups = {
            ('AkkarBommer2010', 'PGA', 0): [rup_id],
            ('AkkarBommer2010', 'PGA', 1): [rup_id],
            ('AkkarBommer2010', 'PGA', 2): [rup_id],
            ('AkkarBommer2010', 'PGA', 3): [rup_id],
            ('AkkarBommer2010', 'PGA', 4): [rup_id],
        }
        expected_gmvs = {
            ('AkkarBommer2010', 'PGA', 0): [0.1027847118266612],
            ('AkkarBommer2010', 'PGA', 1): [0.02726361912605336],
            ('AkkarBommer2010', 'PGA', 2): [0.0862595971325641],
            ('AkkarBommer2010', 'PGA', 3): [0.04727148908077005],
            ('AkkarBommer2010', 'PGA', 4): [0.04750575818347277],
        }
        numpy.testing.assert_equal(calc.ruptures_per_site, expected_rups)
        for i, gmvs in expected_gmvs.iteritems():
            numpy.testing.assert_allclose(gmvs, expected_gmvs[i])

        # 5 curves (one per each site) for 3 levels, 1 IMT
        [(gname, [curves])] = calc.to_haz_curves(
            site_coll.sids, dict(PGA=[0.03, 0.04, 0.05]),
            invest_time=50., num_ses=10)
        self.assertEqual(gname, 'AkkarBommer2010')
        numpy.testing.assert_array_almost_equal(
            curves,
            [[0.09516258, 0.09516258, 0.09516258],  # curve site1
             [0.00000000, 0.00000000, 0.00000000],  # curve site2
             [0.09516258, 0.09516258, 0.09516258],  # curve site3
             [0.09516258, 0.09516258, 0.00000000],  # curve site4
             [0.09516258, 0.09516258, 0.00000000],  # curve site5
             ])


class GmvsToHazCurveTestCase(unittest.TestCase):
    """
    Tests for
    :func:`openquake.engine.calculators.hazard.event_based.\
post_processing.gmvs_to_haz_curve`.
    """

    def test_gmvs_to_haz_curve_site_1(self):
        expected_poes = [0.63578, 0.39347, 0.07965]
        imls = [0.01, 0.1, 0.2]
        gmvs = test_data.SITE_1_GMVS
        invest_time = 1.0  # years
        duration = 1000.0  # years

        actual_poes = core.gmvs_to_haz_curve(gmvs, imls, invest_time, duration)
        numpy.testing.assert_array_almost_equal(
            expected_poes, actual_poes, decimal=6)

    def test_gmvs_to_haz_curve_case_2(self):
        expected_poes = [0.63578, 0.28609, 0.02664]
        imls = [0.01, 0.1, 0.2]
        gmvs = test_data.SITE_2_GMVS
        invest_time = 1.0  # years
        duration = 1000.0  # years

        actual_poes = core.gmvs_to_haz_curve(gmvs, imls, invest_time, duration)
        numpy.testing.assert_array_almost_equal(
            expected_poes, actual_poes, decimal=6)


class UnknownGsimTestCase(unittest.TestCase):
    # the case where the source model contains a TRT which does not
    # exist in the gsim_logic_tree file
    def test(self):
        cfg = helpers.get_data_path('bad_gsim/job.ini')
        job = helpers.get_job(cfg, username=getpass.getuser())
        calc = core.EventBasedHazardCalculator(job)
        with self.assertRaises(ValueError) as ctxt:
            calc.initialize_site_collection()
            calc.initialize_sources()
        errmsg = str(ctxt.exception)
        assert errmsg.startswith(
            "Found in 'source_model.xml' a tectonic region type "
            "'Active Shallow Crust' inconsistent with the ones"), errmsg
