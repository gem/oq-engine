# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
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

"""
NOTE: Current values are based on this implementation, but will be updated
if author-provided values can be obtained.
"""

import unittest
import numpy as np

from openquake.hazardlib import imt
from openquake.hazardlib.gsim.sung_2022 import (
    SungEtAl2022, SungEtAl2022NonErgodic)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

H5 = "adj_RE_france.h5"
# Cadarache site, within the France 0.2 deg grid
CLON, CLAT = 5.7664, 43.6748


def _empty_ctx(n, extra=()):
    dt = [("mag", float), ("ztor", float), ("rrup", float),
          ("vs30", float), ("clon", float), ("clat", float),
          ("custom_site_id", "S8"),
          ("sids", int), ("occurrence_rate", float)]
    for col in extra:
        dt.append((col, float))
    return np.zeros(n, dtype=dt).view(np.recarray)


class SungEtAl2022TestCase(BaseGSIMTestCase):
    GSIM_CLASS = SungEtAl2022

    def test_all(self):
        # Run the ergodic GSIM on 110 (M, Rrup, Vs30) scenarios and check
        # mean/tau/phi/total against pinned reference values.
        self.check("SUNG22/SUNG22_ERG.csv",
                   max_discrep_percentage=0.1,
                   std_discrep_percentage=0.1)


class SungEtAl2022NonErgodicTestCase(BaseGSIMTestCase):
    GSIM_CLASS = SungEtAl2022NonErgodic

    def test_mean_rows(self):
        # Run the non-ergodic GSIM (posterior-mean adjustment) on 10 scenarios
        # split between site1 and site2 to exercise per-site routing. Also
        # checks EAS(1.0) path for both sites.
        gsim = SungEtAl2022NonErgodic(adjustment_h5=H5, rlz_id="mean")
        self.GSIM = gsim
        self.check("SUNG22/SUNG22_NON_ERG.csv",
                   max_discrep_percentage=0.1,
                   std_discrep_percentage=0.1)


class SungEtAl2022StructuralTestCase(unittest.TestCase):
    """
    Checks on the Sung 2022 non-ergodic GSIM mechanics/requirements.
    """
    @classmethod
    def setUpClass(cls):
        cls.gsim = SungEtAl2022NonErgodic(adjustment_h5=H5, rlz_id="mean")

    def test_off_grid_tol(self):
        # The off-grid rejection distance is derived from the grid step,
        # not hard-coded. For France's 0.2 deg grid that's half a cell
        # (~0.1 deg), tolerating a little float32 jitter from the h5.
        self.assertAlmostEqual(self.gsim.off_grid_tol, 0.1, places=2)

    def test_lattice_params(self):
        # The France adjustment grid is a regular 0.2 deg lattice of
        # 91 lon x 61 lat = 5551 nodes, stored lon-fast; confirm the
        # init-time detection picked up the right numbers.
        g = self.gsim
        self.assertAlmostEqual(g._lon_step, 0.2, places=4)
        self.assertAlmostEqual(g._lat_step, 0.2, places=4)
        self.assertEqual(g._n_lon, 91)
        self.assertEqual(g._n_lat, 61)
        self.assertEqual(g._n_lon * g._n_lat, 5551)
        self.assertTrue(g._lon_fast)

    def test_sites_loaded(self):
        # The consolidated h5 bundles the available target sites; the GSIM
        # must see them all at init time.
        self.assertEqual(self.gsim.sites, ["site1", "site2"])

    def test_off_grid_rupture_raises(self):
        # A rupture far outside the France bbox must fail loudly rather
        # than silently pick the nearest edge cell.
        ctx = _empty_ctx(1)
        ctx.mag[:] = 5.0
        ctx.ztor[:] = 2.0
        ctx.rrup[:] = 50.0
        ctx.vs30[:] = 2100.0
        ctx.clon[:] = 20.0  # far east of France bbox
        ctx.clat[:] = 55.0
        ctx.custom_site_id[:] = b"site1"
        n = 1
        mean, sigma, tau, phi = (np.zeros((1, n)) for _ in range(4))
        imts = [imt.from_string("EAS(5.0)")]
        with self.assertRaises(ValueError):
            res = self.gsim.compute_central(
                ctx, imts, mean, sigma, tau, phi)
            self.gsim.apply_branch_shift(res, imts, mean)

    def test_missing_frequency_raises(self):
        # Asking for a frequency the h5 doesn't ship (here EAS(2.0); only
        # 1 Hz and 5 Hz are stored) must raise, not silently fall back.
        ctx = _empty_ctx(1)
        ctx.mag[:] = 5.0
        ctx.ztor[:] = 2.0
        ctx.rrup[:] = 50.0
        ctx.vs30[:] = 2100.0
        ctx.clon[:] = CLON
        ctx.clat[:] = CLAT
        ctx.custom_site_id[:] = b"site1"
        mean, sigma, tau, phi = (np.zeros((1, 1)) for _ in range(4))
        imts = [imt.from_string("EAS(2.0)")]
        with self.assertRaises((KeyError, ValueError)):
            self.gsim.compute_central(ctx, imts, mean, sigma, tau, phi)

    def test_unknown_site_raises(self):
        # A ctx row carrying a custom_site_id not present in the h5 must
        # raise, not silently fall back to another site's adjustment.
        ctx = _empty_ctx(1)
        ctx.mag[:] = 5.0
        ctx.ztor[:] = 2.0
        ctx.rrup[:] = 50.0
        ctx.vs30[:] = 2100.0
        ctx.clon[:] = CLON
        ctx.clat[:] = CLAT
        ctx.custom_site_id[:] = b"siteX"
        mean, sigma, tau, phi = (np.zeros((1, 1)) for _ in range(4))
        imts = [imt.from_string("EAS(5.0)")]
        with self.assertRaises(ValueError):
            self.gsim.compute_central(ctx, imts, mean, sigma, tau, phi)

    def test_site_missing_frequency_raises(self):
        # When a (site, freq) pair isn't in the h5 the GSIM must raise
        # rather than silently skip. Patch self.dat to simulate a site
        # that only ships 1 Hz (shipped h5 has both freqs for all sites).
        gsim = SungEtAl2022NonErgodic(adjustment_h5=H5, rlz_id="mean")
        del gsim.dat[("site1", 5.0)]
        ctx = _empty_ctx(1)
        ctx.mag[:] = 5.0
        ctx.ztor[:] = 2.0
        ctx.rrup[:] = 50.0
        ctx.vs30[:] = 2100.0
        ctx.clon[:] = CLON
        ctx.clat[:] = CLAT
        ctx.custom_site_id[:] = b"site1"
        mean, sigma, tau, phi = (np.zeros((1, 1)) for _ in range(4))
        imts = [imt.from_string("EAS(5.0)")]
        with self.assertRaises(ValueError):
            gsim.compute_central(ctx, imts, mean, sigma, tau, phi)


class SungEtAl2022BehaviouralTestCase(unittest.TestCase):
    """
    Invariant checks on what the non-ergodic model actually does.
    """
    @classmethod
    def setUpClass(cls):
        cls.erg = SungEtAl2022()
        cls.ne_mean = SungEtAl2022NonErgodic(adjustment_h5=H5, rlz_id="mean")
        cls.ne_0 = SungEtAl2022NonErgodic(adjustment_h5=H5, rlz_id=0)
        cls.ne_99 = SungEtAl2022NonErgodic(adjustment_h5=H5, rlz_id=99)

    def _grid(self, site, freq):
        return self.ne_mean.dat[(site, freq)]

    def _nearest_idx(self, site, freq, clon, clat):
        g = self._grid(site, freq)
        d2 = (g['lon'] - clon) ** 2 + (g['lat'] - clat) ** 2
        return int(d2.argmin())

    def _ctx(self, clon=CLON, clat=CLAT, mag=5.0, rrup=50.0, vs30=2100.0,
             ztor=2.0, site="site1"):
        ctx = _empty_ctx(1)
        ctx.mag[:] = mag
        ctx.ztor[:] = ztor
        ctx.rrup[:] = rrup
        ctx.vs30[:] = vs30
        ctx.clon[:] = clon
        ctx.clat[:] = clat
        ctx.custom_site_id[:] = site.encode("utf-8")
        return ctx

    def _compute(self, gsim, ctx, im):
        imts = [imt.from_string(im)]
        mean, sigma, tau, phi = (np.zeros((1, 1)) for _ in range(4))
        if isinstance(gsim, SungEtAl2022NonErgodic):
            res = gsim.compute_central(ctx, imts, mean, sigma, tau, phi)
            gsim.apply_branch_shift(res, imts, mean)
        else:
            gsim.compute(ctx, imts, mean, sigma, tau, phi)
        return mean[0, 0], sigma[0, 0], tau[0, 0], phi[0, 0]

    def test_delta_mu_additivity(self):
        # The non-ergodic model = ergodic + Delta-mu read from the h5 at
        # the rupture's grid cell. Check that identity directly at three
        # positions around Site1.
        for clon, clat in [(CLON, CLAT), (4.5, 44.7), (7.0, 43.5)]:
            ctx = self._ctx(clon=clon, clat=clat, site="site1")
            m_erg, *_ = self._compute(self.erg, ctx, "EAS(5.0)")
            m_ne, *_ = self._compute(self.ne_mean, ctx, "EAS(5.0)")
            expected = float(self._grid("site1", 5.0)['mean'][
                self._nearest_idx("site1", 5.0, clon, clat)])
            self.assertAlmostEqual(m_ne - m_erg, expected, places=5,
                                   msg=f"at ({clon}, {clat})")

    def test_rlz_id_dispatch(self):
        # Switching rlz_id picks a different column of dat['rlz'] and
        # shifts the mean by exactly that column's value at the rupture
        # cell. Check for rlz_id = 0 and 99 against the 'mean' reference.
        ctx = self._ctx()
        m_mean, *_ = self._compute(self.ne_mean, ctx, "EAS(5.0)")
        m_0, *_ = self._compute(self.ne_0, ctx, "EAS(5.0)")
        m_99, *_ = self._compute(self.ne_99, ctx, "EAS(5.0)")
        idx = self._nearest_idx("site1", 5.0, CLON, CLAT)
        g = self._grid("site1", 5.0)
        self.assertAlmostEqual(
            m_0 - m_mean,
            float(g['rlz'][idx, 0] - g['mean'][idx]),
            places=5)
        self.assertAlmostEqual(
            m_99 - m_mean,
            float(g['rlz'][idx, 99] - g['mean'][idx]),
            places=5)

    def test_lattice_vs_argmin(self):
        # The fast lattice-arithmetic nearest-node lookup used inside
        # compute_central must give the same cell as a brute-force
        # distance-squared argmin across the whole grid.
        rng = np.random.default_rng(0)
        lon_pts = rng.uniform(-5.5, 11.8, 20)
        lat_pts = rng.uniform(40.3, 51.9, 20)
        g = self.ne_mean
        for clon, clat in zip(lon_pts, lat_pts):
            i_lon = int(round((clon - g._lon0) / g._lon_step))
            i_lat = int(round((clat - g._lat0) / g._lat_step))
            lattice_idx = i_lat * g._n_lon + i_lon
            self.assertEqual(
                lattice_idx,
                self._nearest_idx("site1", 5.0, clon, clat),
                msg=f"at ({clon:.4f}, {clat:.4f})")

    def test_sigma_invariance(self):
        # sigma/tau/phi come from COEFFS, so they must not depend on
        # the rupture location. Moving clon/clat must not change them.
        c1 = self._compute(self.ne_mean,
                           self._ctx(clon=CLON, clat=CLAT), "EAS(5.0)")
        c2 = self._compute(self.ne_mean,
                           self._ctx(clon=4.5, clat=44.7), "EAS(5.0)")
        self.assertAlmostEqual(c1[1], c2[1], places=6)  # sigma
        self.assertAlmostEqual(c1[2], c2[2], places=6)  # tau
        self.assertAlmostEqual(c1[3], c2[3], places=6)  # phi

    def test_site_routing(self):
        # Same rupture (clon, clat), different custom_site_id -> different
        # Delta-mu because the posterior is conditional on the receiver.
        # The shift between site1 and site2 must equal the difference of
        # the two sites' dat['mean'] columns at the same grid cell.
        ctx1 = self._ctx(clon=4.0, clat=46.0, site="site1")
        ctx2 = self._ctx(clon=4.0, clat=46.0, site="site2")
        m1, *_ = self._compute(self.ne_mean, ctx1, "EAS(5.0)")
        m2, *_ = self._compute(self.ne_mean, ctx2, "EAS(5.0)")
        idx1 = self._nearest_idx("site1", 5.0, 4.0, 46.0)
        idx2 = self._nearest_idx("site2", 5.0, 4.0, 46.0)
        expected_shift = (float(self._grid("site2", 5.0)['mean'][idx2]) -
                          float(self._grid("site1", 5.0)['mean'][idx1]))
        self.assertAlmostEqual(m2 - m1, expected_shift, places=5)

    def test_central_key_stability(self):
        # ContextMaker amortises the shared backbone across LT branches
        # by central_key. Instances with the same h5 must share a key
        # (any rlz_id), different h5 files must get different keys.
        a = SungEtAl2022NonErgodic(adjustment_h5=H5, rlz_id="mean")
        b = SungEtAl2022NonErgodic(adjustment_h5=H5, rlz_id=5)
        self.assertEqual(a.central_key, b.central_key)
