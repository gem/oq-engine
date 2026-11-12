# The Hazard Library
# Copyright (C) 2026, GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import os
import csv
import tempfile
import unittest
import numpy as np
from types import SimpleNamespace

from openquake.baselib import InvalidFile
from openquake.commonlib import readinput
from openquake.hazardlib import valid
from openquake.hazardlib.contexts import simple_cmaker
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib.gsim.mgmpe.modifiable_gmpe import ModifiableGMPE
from openquake.hazardlib.gsim.mgmpe.swiss_amplification import (
    apply_swiss_amplification_sa, apply_swiss_site_specific_amplification_sa)


FIELDS = {
    0.2: ('ch_ampl02', 'ch_phis2s02', 'ch_phiss02'),
    0.3: ('ch_ampl03', 'ch_phis2s03', 'ch_phiss03'),
    0.4: ('ch_ampl04', 'ch_phis2s04', 'ch_phiss04'),
    0.6: ('ch_ampl06', 'ch_phis2s06', 'ch_phiss06'),
}
NAME = 'apply_swiss_site_specific_amplification_sa'
MODEL = 'EdwardsFah2013Foreland10Bars'
# Pythagorean component pairs and their independently known phi values.
# Different periods must produce different uncertainties, not only means.
PHI_CASES = {0.2: (0.3, 0.4, 0.5), 0.3: (0.5, 1.2, 1.3),
             0.4: (0.6, 0.8, 1.0), 0.6: (0.8, 1.5, 1.7)}


def assert_close(actual, expected):
    # Allow float64 roundoff, far below the supplied correction differences.
    np.testing.assert_allclose(actual, expected, rtol=1e-10, atol=1e-12,
                               equal_nan=False)


def new_gsim(periods=(0.2, 0.3, 0.4, 0.6), **modifiers):
    # Use the real public configuration path, not an isolated helper mock.
    return ModifiableGMPE(
        gmpe={MODEL: {}}, **{NAME: {'periods': periods}}, **modifiers)


def new_context(cmaker, periods):
    # Distinct means and phi values expose wrong period-to-column mappings.
    ctx = cmaker.new_ctx(3)
    ctx.mag = 6.
    ctx.rrup = [1., 10., 30.]
    ctx.vs30 = 1105.
    for i, period in enumerate(periods):
        ampl, s2s, ss = FIELDS[period]
        phi_s2s, phi_ss, phi_star = PHI_CASES[period]
        ctx[ampl] = [0.1 * (i + 1), 0., -0.1]
        ctx[s2s] = [phi_s2s, 0., phi_s2s]
        ctx[ss] = [phi_ss, phi_star, phi_ss]
    return ctx


class SwissAmplificationTestCase(unittest.TestCase):
    """
    Tests the implementation of a correction factor for intensity
    """
    def get_ctx(self, cmaker):
        ctx = cmaker.new_ctx(4)
        ctx.mag = 6.0
        ctx.hypo_depth = 10.
        ctx.amplfactor = [-1.0, 1.5, 0.00, -1.99]
        ctx.ch_ampl03 = [-0.2, 0.4, 0.6, 0]
        ctx.ch_phis2s03 = [0.3, 0.4, 0.5, 0.2]
        ctx.ch_phiss03 = [0.2, 0.1, 0.3, 0.4]
        ctx.rhypo = ctx.rrup = ctx.repi = np.array([1., 10., 30., 70.])
        return ctx

    def test(self):
        for gmpe_name in ['ECOS2009', 'BindiEtAl2011RepiFixedH',
                          'BaumontEtAl2018High2210IAVGDC30n7',
                          'FaccioliCauzzi2006']:

            gmpe = valid.gsim(gmpe_name)
            gmm = valid.modified_gsim(gmpe, apply_swiss_amplification={})
            cmaker = simple_cmaker([gmm, gmpe], ['MMI'])
            ctx = self.get_ctx(cmaker)
            mea, _sig, _tau, phi = cmaker.get_mean_stds([ctx])
            exp_mean = mea[1] + np.array([-1.00, 1.50, 0, -1.99])

            # Check the computed mean + amplification
            np.testing.assert_almost_equal(mea[0], exp_mean)

        for gmpe_name in ['EdwardsFah2013Alpine10Bars',
                          'EdwardsFah2013Foreland60Bars',
                          'ChiouYoungs2008SWISS01']:

            gmpe = valid.gsim(gmpe_name)
            gmm = valid.modified_gsim(gmpe, apply_swiss_amplification_sa={})
            cmaker = simple_cmaker([gmm, gmpe], ['SA(0.3)'])
            ctx = self.get_ctx(cmaker)
            mea, _sig, _tau, phi = cmaker.get_mean_stds([ctx])
            exp_mean = mea[1] + np.array([-0.2, 0.4, 0.6, 0])
            exp_stdev = np.sqrt(np.array([0.3, 0.4, 0.5, 0.2])**2 +
                                np.array([0.2, 0.1, 0.3, 0.4])**2)

            # Check the computed mean + amplification
            np.testing.assert_array_almost_equal(mea[0], exp_mean)

            # Check the computed intra-event stdev
            np.testing.assert_array_almost_equal(phi[0], [exp_stdev])


class SwissSiteSpecificAmplificationTestCase(unittest.TestCase):
    def test_independent_reference(self):
        # Hand-worked Pythagorean cases, independent of the implementation:
        # phi=(.5,.5,1), total=sqrt((.2,.3,.5)^2+phi^2).
        ctx = SimpleNamespace(
            ch_ampl02=np.array([0.2, 0., -0.1]),
            ch_phis2s02=np.array([0.3, 0., 0.6]),
            ch_phiss02=np.array([0.4, 0.5, 0.8]))
        mean = np.array([-1., -2., -3.])
        sigma, phi = np.zeros(3), np.zeros(3)
        tau = np.array([0.2, 0.3, 0.5])
        apply_swiss_site_specific_amplification_sa(
            ctx, SA(0.2), mean, sigma, tau, phi, periods=[0.2])
        assert_close(mean, [-0.8, -2., -3.1])
        assert_close(phi, [0.5, 0.5, 1.])
        assert_close(tau, [0.2, 0.3, 0.5])
        assert_close(sigma, np.sqrt([0.29, 0.34, 1.25]))

    def test_selected_periods_and_instance_isolation(self):
        original = valid.gsim(MODEL)
        requirements = original.REQUIRES_SITES_PARAMETERS
        for periods in ([0.2], [0.2, 0.4, 0.6], list(FIELDS)):
            with self.subTest(periods=periods):
                modified = new_gsim(periods)
                fields = {f for p in periods for f in FIELDS[p]}
                self.assertEqual(modified.REQUIRES_SITES_PARAMETERS,
                                 requirements | fields)
                cmaker = simple_cmaker(
                    [modified, original], ['SA(%s)' % p for p in periods])
                self.assertEqual(cmaker.REQUIRES_SITES_PARAMETERS,
                                 requirements | fields | {'vs30'})
                ctx = new_context(cmaker, periods)
                mean, sigma, tau, phi = cmaker.get_mean_stds([ctx])
                for m, period in enumerate(periods):
                    phi_star = PHI_CASES[period][2]
                    assert_close(mean[0, m] - mean[1, m],
                                 ctx[FIELDS[period][0]])
                    assert_close(phi[0, m], phi_star)
                    assert_close(sigma[0, m],
                                 np.hypot(tau[1, m], phi_star))
                assert_close(tau[0], tau[1])
        self.assertEqual(original.REQUIRES_SITES_PARAMETERS, requirements)
        self.assertEqual(new_gsim([0.4]).REQUIRES_SITES_PARAMETERS,
                         requirements | set(FIELDS[0.4]))
        self.assertEqual(ModifiableGMPE.REQUIRES_SITES_PARAMETERS, set())
        defaults = ModifiableGMPE(gmpe={MODEL: {}}, **{NAME: {}})
        all_fields = {f for fs in FIELDS.values() for f in fs}
        self.assertEqual(defaults.REQUIRES_SITES_PARAMETERS,
                         requirements | all_fields)

    def test_legacy_swiss_equivalence(self):
        # Cover both legacy periods and all four outputs, not just SA(.3) mean.
        old = valid.modified_gsim(
            valid.gsim(MODEL), apply_swiss_amplification_sa={})
        new = new_gsim([0.3, 0.6])
        cmaker = simple_cmaker([old, new], ['SA(0.3)', 'SA(0.6)'])
        outputs = cmaker.get_mean_stds([new_context(cmaker, [0.3, 0.6])])
        for output in outputs:
            assert_close(output[0], output[1])
        self.assertFalse(any('02' in p or '04' in p
                             for p in cmaker.REQUIRES_SITES_PARAMETERS))

    def test_pga_compatibility(self):
        # PGA reads no SA columns. Its incoming total deliberately disagrees
        # with tau/phi so this verifies reconstruction, not a complete no-op.
        mean, sigma = np.array([-1., -2.]), np.full(2, 9.)
        tau, phi = np.array([0.3, 0.6]), np.array([0.4, 0.8])
        apply_swiss_site_specific_amplification_sa(
            SimpleNamespace(), PGA(), mean, sigma, tau, phi)
        assert_close(mean, [-1., -2.])
        assert_close(phi, [0.4, 0.8])
        assert_close(tau, [0.3, 0.6])
        assert_close(sigma, [0.5, 1.])
        for value in (np.nan, -0.1):
            with self.subTest(phi=value):
                with self.assertRaises(ValueError):
                    apply_swiss_site_specific_amplification_sa(
                        SimpleNamespace(), PGA(), mean, sigma, tau,
                        np.array([value, 0.8]))

        # Adding PGA neither adds site columns nor changes selected SA output.
        periods = [0.2, 0.4, 0.6]
        modified, original = new_gsim(periods), valid.gsim(MODEL)
        sa_imts = ['SA(%s)' % p for p in periods]
        mixed = simple_cmaker([modified, original], ['PGA'] + sa_imts)
        sa_only = simple_cmaker([modified], sa_imts)
        self.assertEqual(mixed.REQUIRES_SITES_PARAMETERS,
                         sa_only.REQUIRES_SITES_PARAMETERS)
        outputs = mixed.get_mean_stds([new_context(mixed, periods)])
        mean, sigma, tau, phi = outputs
        pga = mixed.imts.index(PGA())
        for output in (mean, tau, phi):
            assert_close(output[0, pga], output[1, pga])
        assert_close(sigma[0, pga], np.hypot(tau[1, pga], phi[1, pga]))
        expected = sa_only.get_mean_stds([new_context(sa_only, periods)])
        for m, imt in enumerate(sa_only.imts):
            for actual, reference in zip(outputs, expected):
                assert_close(actual[0, mixed.imts.index(imt)], reference[0, m])

    def test_legacy_unsupported_periods(self):
        for imt in (PGA(), PGV(), SA(0.2), SA(0.4), SA(0.5)):
            with self.subTest(imt=imt):
                with self.assertRaisesRegex(ValueError, 'supported periods'):
                    apply_swiss_amplification_sa(
                        SimpleNamespace(), imt, *np.zeros((4, 1)))

    def test_uncertainty_numerical_range(self):
        # Scaled Pythagorean triples retain finite, nonzero results even when
        # squaring the inputs would overflow or underflow float64.
        scale = np.array([1e200, 1e-200])
        ctx = SimpleNamespace(
            ch_ampl03=np.zeros(2), ch_phis2s03=0.3 * scale,
            ch_phiss03=0.4 * scale)
        for modifier, imt in (
                (apply_swiss_amplification_sa, SA(0.3)),
                (apply_swiss_site_specific_amplification_sa, SA(0.3)),
                (apply_swiss_site_specific_amplification_sa, PGA())):
            with self.subTest(modifier=modifier.__name__, imt=imt):
                outputs = np.zeros((4, 2))
                outputs[2], outputs[3] = 1.2 * scale, 0.5 * scale
                with np.errstate(over='raise', under='raise', invalid='raise'):
                    modifier(ctx, imt, *outputs)
                assert_close(outputs[3] / scale, 0.5)
                assert_close(outputs[1] / scale, 1.3)

    def test_invalid_configuration(self):
        # Representative empty, duplicate, unsupported and boolean choices.
        for periods in ([], [0.2, 0.2], [0.5], [True], [np.nan],
                        [np.inf], [-np.inf], ['0.2'], [[0.2]], None, 0.2):
            with self.subTest(periods=periods):
                with self.assertRaises(ValueError):
                    new_gsim(periods)
        with self.assertRaises(ValueError):
            new_gsim([0.3], apply_swiss_amplification_sa={})
        with self.assertRaises(ValueError):
            ModifiableGMPE(gmpe={'Campbell2003': {}}, **{NAME: {}})

    def test_invalid_inputs(self):
        cmaker = simple_cmaker([new_gsim([0.2])], ['SA(0.2)'])
        ctx = new_context(cmaker, [0.2])
        outputs = np.zeros((4, 3))
        outputs[2] = 0.2
        # Test this modifier's domain, not a base coefficient table's errors.
        for imt in (PGV(), SA(0.3), SA(0.2, 10.)):
            with self.subTest(imt=imt):
                with self.assertRaises(ValueError):
                    apply_swiss_site_specific_amplification_sa(
                        ctx, imt, *outputs, periods=[0.2])
        cases = [('ch_ampl02', np.nan), ('ch_phis2s02', np.inf),
                 ('ch_phis2s02', -0.1), ('ch_phiss02', -0.1),
                 ('tau', np.nan), ('tau', -0.1)]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                ctx = new_context(cmaker, [0.2])
                outputs[2] = 0.2
                if field == 'tau':
                    outputs[2, 0] = value
                else:
                    ctx[field][0] = value
                with self.assertRaisesRegex(ValueError, field):
                    apply_swiss_site_specific_amplification_sa(
                        ctx, SA(0.2), *outputs, periods=[0.2])


class SwissSiteSpecificSiteInputTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write_sites(self, periods, missing=None, zero=False):
        fields = ['lon', 'lat', 'vs30'] + [
            f for p in periods for f in FIELDS[p] if f != missing]
        filename = os.path.join(self.tmp.name, 'sites.csv')
        values = {'lon': 7., 'lat': 47., 'vs30': 1105.}
        for period in periods:
            ampl, s2s, ss = FIELDS[period]
            values.update({ampl: 0. if zero else 0.2, s2s: 0.3, ss: 0.4})
        with open(filename, 'w', newline='', encoding='utf8') as out:
            writer = csv.DictWriter(out, fieldnames=fields,
                                    extrasaction='ignore')
            writer.writeheader()
            writer.writerow(values)
        return filename

    def load_sites(self, filename, required):
        oq = SimpleNamespace(
            req_site_params=required, impact=False, override_vs30=False,
            site_labels={}, inputs={'site_model': [filename]})
        sm = readinput.get_site_model(oq)
        sites = SiteCollection.from_points(
            sm['lon'], sm['lat'], req_site_params=required)
        sites.assoc(sm, 5., 'strict')
        return sites

    def test_selected_site_columns(self):
        periods = [0.2, 0.4, 0.6]
        gsim = new_gsim(periods)
        cmaker = simple_cmaker([gsim], ['SA(%s)' % p for p in periods])
        sites = self.load_sites(self.write_sites(periods, zero=True),
                                gsim.REQUIRES_SITES_PARAMETERS)
        self.assertNotIn('ch_ampl03', sites.array.dtype.names)
        ctx = cmaker.new_ctx(1)
        ctx.mag, ctx.rrup = 6., 10.
        for field in gsim.REQUIRES_SITES_PARAMETERS:
            ctx[field] = sites.array[field]
        mean, sigma, tau, phi = cmaker.get_mean_stds([ctx])
        self.assertTrue(np.isfinite(mean).all())
        assert_close(phi, 0.5)
        assert_close(sigma**2, tau**2 + 0.25)
        filename = self.write_sites(periods, missing='ch_phiss04')
        # Keep the native loader diagnostics; this extension does not promise
        # a new error type for a missing local-only site column.
        with self.assertRaisesRegex((KeyError, InvalidFile), 'ch_phiss04'):
            self.load_sites(filename, gsim.REQUIRES_SITES_PARAMETERS)
        # Allow zero corrections without weakening unrelated site validation.
        sm = sites.array.copy()
        sm['vs30'] = 0.
        with self.assertRaises(ValueError):
            sites.assoc(sm, 5., 'strict')
