# ruff: noqa: E402
"""
Unit tests for Moss et al. (2022) reverse-fault PFDHA models.

All expected values are computed analytically from GIRS-2022-05 coefficients.
Tolerance: 2 % relative for analytical equations.
"""
import math
import numpy as np
import pytest
from scipy import stats


# =====================================================================
# Primary FD
# =====================================================================
from openquake.pfd.primary_surf_displ.moss2022 import (
    Moss2022PrimaryFD, SCALING, GAMMA_REGRESSION, GAMMA_GLOBAL,
)


class TestMoss2022PrimaryFDReportReferences:
    """Primary-FD values stated in GIRS-2022-05."""

    def test_equations_4_2_4_3_global_gamma_parameters(self):
        """Preferred gamma parameters from Eqs. 4.2-4.3."""
        assert GAMMA_GLOBAL == {
            'AD': {'a': 2.54199, 'b': 0.393391},
            'MD': {'a': 2.11095, 'b': 0.180981},
        }

    def test_appendix_c_gamma_regression_parameters(self):
        """D/AD and D/MD gamma regressions from Appendix C source."""
        assert GAMMA_REGRESSION == {
            'AD': {'a1': 4.2797, 'a2': 1.6216,
                   'b1': -0.5003, 'b2': 0.5133},
            'MD': {'a1': 1.4244, 'a2': 1.856,
                   'b1': -0.0832, 'b2': 0.1994},
        }

    def test_table_4_4_scaling_parameters(self):
        """AD/MD magnitude-scaling rows from Table 4.4."""
        assert SCALING == {
            'AD': {
                'complete': {'a': -2.87, 'b': 0.416,
                             's': 0.133, 's_rec': 0.20},
                'all': {'a': -2.98, 'b': 0.427,
                        's': 0.181, 's_rec': 0.25},
            },
            'MD': {
                'complete': {'a': -2.50, 'b': 0.415,
                             's': 0.148, 's_rec': 0.20},
                'incomplete': {'a': -2.71, 'b': 0.354,
                               's': 0.305, 's_rec': 0.35},
                'all': {'a': -2.73, 'b': 0.422,
                        's': 0.354, 's_rec': None},
            },
        }

    @pytest.mark.parametrize(
        "version, x_l, expected_shape, expected_scale", [
            ("AD", 0.0, 1.6216, 0.5133),
            ("AD", 0.5, 3.76145, 0.26315),
            ("MD", 0.0, 1.856, 0.1994),
            ("MD", 0.5, 2.5682, 0.1578),
        ])
    def test_appendix_c_gamma_parameter_reference_values(
            self, version, x_l, expected_shape, expected_scale):
        """Exact x/L examples from the Appendix C regression formulae."""
        c = GAMMA_REGRESSION[version]
        shape = c['a1'] * x_l + c['a2']
        scale = c['b1'] * x_l + c['b2']
        assert shape == pytest.approx(expected_shape, abs=1e-12)
        assert scale == pytest.approx(expected_scale, abs=1e-12)


class TestMoss2022PrimaryFDProduction:
    """Direct numerical checks for the production principal-FD model."""


    def setup_method(self):
        self.model = Moss2022PrimaryFD()

    def test_md_regression_reference_values(self):
        """Regression anchor for P(D > d | M, x/L), MD/regression branch."""
        p = np.asarray(self.model.get_prob(
            d=[0.01, 0.1, 1.0],
            X_L_ratio=[0.0, 0.25, 0.5],
            mag=7.0,
            version="MD",
            completeness="complete",
            gamma_mode="regression",
            sigma_type="recommended",
        ))
        expected = np.array([
            [0.99943149, 0.99985097, 0.99995734],
            [0.96597570, 0.98071276, 0.98820701],
            [0.35814380, 0.39659952, 0.41930456],
        ])
        assert p.shape == (3, 3)
        assert np.allclose(p, expected, rtol=1e-7, atol=1e-10)

    def test_ad_global_reference_values_are_xl_independent(self):
        """Regression anchor for the AD/global gamma branch."""
        p = np.asarray(self.model.get_prob(
            d=[0.01, 0.1, 1.0],
            X_L_ratio=[0.0, 0.25, 0.5],
            mag=7.0,
            version="AD",
            completeness="complete",
            gamma_mode="global",
            sigma_type="regression",
        ))
        expected = np.array([
            [0.99997373, 0.99997373, 0.99997373],
            [0.99246138, 0.99246138, 0.99246138],
            [0.47124574, 0.47124574, 0.47124574],
        ])
        assert p.shape == (3, 3)
        assert np.allclose(p, expected, rtol=1e-7, atol=1e-10)

    def test_xl_folding_symmetry(self):
        """x/L and 1-x/L should give the same principal displacement curve."""
        p_left = self.model.get_prob(d=[0.01, 0.1, 1.0],
                                     X_L_ratio=[0.25], mag=7.0)
        p_right = self.model.get_prob(d=[0.01, 0.1, 1.0],
                                      X_L_ratio=[0.75], mag=7.0)
        assert np.allclose(p_left, p_right, rtol=1e-12, atol=0.0)

    def test_shape_is_displacement_by_site(self):
        p = np.asarray(self.model.get_prob(
            d=[0.01, 0.1],
            X_L_ratio=[0.1, 0.5, 0.9],
            mag=7.0,
        ))
        assert p.shape == (2, 3)

    def test_prob_decreases_with_displacement(self):
        p = np.asarray(self.model.get_prob(
            d=[0.001, 0.01, 0.1, 1.0],
            X_L_ratio=[0.5],
            mag=7.0,
        )).flatten()
        assert np.all(np.diff(p) <= 1e-12)

    @pytest.mark.parametrize("kwargs", [
        {"version": "XX"},
        {"version": "AD", "completeness": "incomplete"},
        {"gamma_mode": "unknown"},
        {"sigma_type": "unknown"},
        {"X_L_ratio": [-0.1]},
        {"X_L_ratio": [1.1]},
    ])
    def test_invalid_options_raise(self, kwargs):
        base = {"d": [0.1], "X_L_ratio": [0.5], "mag": 7.0}
        base.update(kwargs)
        with pytest.raises(ValueError):
            self.model.get_prob(**base)

    def test_rejects_vector_magnitude(self):
        with pytest.raises(ValueError):
            self.model.get_prob(d=[0.1], X_L_ratio=[0.5],
                                mag=[6.5, 7.0])


# =====================================================================
# Secondary SR
# =====================================================================
from openquake.pfd.secondary_surf_rup.moss2022 import Moss2022SecondarySR


class TestMoss2022SecondarySR:
    """Equation 5.5 / Table 5.3 analytical values."""

    def setup_method(self):
        self.model = Moss2022SecondarySR()

    @pytest.mark.parametrize("r_km, expected_hw, expected_fw", [
        (0.0, 1.0, 1.0),
        (0.5, math.exp(-2.2 * 0.5 + 0.5), math.exp(-2.4 * 0.5 + 0.4)),
        (1.0, math.exp(-2.2 * 1.0 + 0.5), math.exp(-2.4 * 1.0 + 0.4)),
        (2.0, math.exp(-2.2 * 2.0 + 0.5), math.exp(-2.4 * 2.0 + 0.4)),
    ])
    def test_simple_method_values(self, r_km, expected_hw, expected_fw):
        p_hw = float(self.model.get_prob(r=r_km, rx=0.1))
        p_fw = float(self.model.get_prob(r=r_km, rx=-0.1))
        assert p_hw == pytest.approx(expected_hw, rel=0.02)
        assert p_fw == pytest.approx(expected_fw, rel=0.02)

    def test_vectorized(self):
        r = np.array([0.0, 0.5, 1.0, 2.0])
        rx = np.array([0.1, 0.1, -0.1, -0.1])
        p = self.model.get_prob(r=r, rx=rx)
        assert p.shape == (4,)
        assert np.all(p >= 0) and np.all(p <= 1)

    def test_biexp_requires_mag(self):
        with pytest.raises(ValueError):
            self.model.get_prob(r=0.5, rx=0.1, method="biexp")

    @pytest.mark.parametrize("r_km, rx, mag, expected", [
        (0.1, 0.1, 7.2, 0.9118305884),
        (0.5, 0.1, 7.2, 0.6672961255),
        (1.0, 0.1, 6.5, 0.2349814234),
        (0.5, -0.1, 6.5, 0.3982218308),
        (0.5, 0.1, 5.5, 0.0),
        (0.5, -0.1, 5.5, 0.0),
    ])
    def test_biexp_reference_values(self, r_km, rx, mag, expected):
        p = self.model.get_prob(r=r_km, rx=rx, mag=mag, method="biexp")
        assert float(p) == pytest.approx(expected, rel=1e-8, abs=1e-12)

    def test_biexp_mag_below_table_range_returns_zero(self):
        p = self.model.get_prob(r=np.array([0.5, 1.0]),
                                rx=np.array([0.1, -0.1]),
                                mag=4.9, method="biexp")
        assert np.all(p == 0.0)


# =====================================================================
# Secondary FD
# =====================================================================
from openquake.pfd.secondary_surf_displ.moss2022 import (
    Moss2022SecondaryFD, ENVELOPE_50, ENVELOPE_85,
)


class TestEnvelopeCoefficients:
    """Spot-check envelope values from Tables 5.7–5.8."""

    def test_simple_hw_50_at_r0(self):
        ec = ENVELOPE_50['simple']['hw']
        val = ec['c'] * math.exp(ec['d'] * 0.0)
        assert val == pytest.approx(0.245, rel=1e-6)

    def test_simple_fw_85_at_r0(self):
        ec = ENVELOPE_85['simple']['fw']
        val = ec['c'] * math.exp(ec['d'] * 0.0)
        assert val == pytest.approx(0.68, rel=1e-6)

    def test_envelope_decays_with_distance(self):
        ec = ENVELOPE_85['simple']['hw']
        val_0 = ec['c'] * math.exp(ec['d'] * 0.0)
        val_5 = ec['c'] * math.exp(ec['d'] * 5.0)
        assert val_5 < val_0

    @pytest.mark.parametrize(
        "table, faulting, side, r_km, expected", [
            (ENVELOPE_50, "simple", "fw", 1.0, 0.245 * math.exp(-0.18)),
            (ENVELOPE_50, "simple", "hw", 1.0, 0.245 * math.exp(-0.34)),
            (ENVELOPE_50, "complex", "fw", 1.0, 0.245 * math.exp(-0.09)),
            (ENVELOPE_50, "complex", "hw", 1.0, 0.245 * math.exp(-0.015)),
            (ENVELOPE_85, "simple", "fw", 1.0, 0.68 * math.exp(-0.13)),
            (ENVELOPE_85, "simple", "hw", 1.0, 0.43 * math.exp(-0.40)),
            (ENVELOPE_85, "complex", "fw", 1.0, 0.68 * math.exp(-0.13)),
            (ENVELOPE_85, "complex", "hw", 1.0, 0.43 * math.exp(-0.012)),
        ])
    def test_table_5_7_5_8_envelope_values(
            self, table, faulting, side, r_km, expected):
        ec = table[faulting][side]
        assert ec['c'] * math.exp(ec['d'] * r_km) == pytest.approx(
            expected, rel=1e-12)


class TestMoss2022SecondaryFDBasic:
    """Smoke tests for the secondary FD model."""

    def setup_method(self):
        self.model = Moss2022SecondaryFD()

    def test_gamma_method_returns_valid_prob(self):
        d = np.array([0.001, 0.01, 0.1, 1.0])
        r = np.array([0.5])
        rx = np.array([0.1])
        p = self.model.get_prob(d=d, mag=6.5, r=r, rx=rx)
        p_arr = np.atleast_1d(p)
        assert np.all(p_arr >= 0) and np.all(p_arr <= 1)

    def test_envelope_method_returns_valid_prob(self):
        d = np.array([0.001, 0.01, 0.1, 1.0])
        r = np.array([0.5])
        rx = np.array([0.1])
        p = self.model.get_prob(d=d, mag=6.5, r=r, rx=rx, method="envelope")
        p_arr = np.atleast_1d(p)
        assert np.all(p_arr >= 0) and np.all(p_arr <= 1)

    def test_envelope_method_matches_eq_5_8_lognormal_survival(self):
        """Envelope mode is exactly MD * d/MD(r) from Eq. 5.8."""
        d = np.array([0.01, 0.1, 0.25])
        mag = 7.5
        r_km = 0.1
        env = ENVELOPE_85['simple']['hw']['c'] * math.exp(
            ENVELOPE_85['simple']['hw']['d'] * r_km)
        sc = SCALING['MD']['complete']
        mu = sc['a'] + sc['b'] * mag
        sigma = sc['s_rec']
        expected = 1.0 - stats.norm.cdf((np.log10(d / env) - mu) / sigma)
        p = np.atleast_1d(self.model.get_prob(
            d=d, mag=mag, r=np.array([r_km]), rx=np.array([0.1]),
            version='MD', completeness='complete', sigma_type='recommended',
            faulting='simple', percentile='85', method='envelope',
        )).flatten()
        assert np.allclose(p, expected, rtol=1e-12, atol=1e-12)

    def test_gamma_method_reference_values_multi_site(self):
        """Regression anchor for the distributed-FD gamma branch."""
        p = np.asarray(self.model.get_prob(
            d=[0.01, 0.1, 1.0],
            mag=7.0,
            r=[0.1, 0.5, 1.0],
            rx=[0.1, 0.1, -0.1],
            version="MD",
            method="gamma",
        ))
        expected = np.array([
            [0.99980681, 0.97965625, 0.40960285],
            [0.99973645, 0.97316188, 0.34784402],
            [0.99989942, 0.98874488, 0.53256383],
        ])
        assert p.shape == (3, 3)
        assert np.allclose(p, expected, rtol=1e-7, atol=1e-10)

    def test_envelope_method_reference_values_multi_site(self):
        """Regression anchor for the distributed-FD deterministic branch."""
        p = np.asarray(self.model.get_prob(
            d=[0.01, 0.1, 1.0],
            mag=7.0,
            r=[0.1, 0.5, 1.0],
            rx=[0.1, 0.1, -0.1],
            version="MD",
            method="envelope",
        ))
        expected = np.array([
            [1.0, 0.99999984, 0.54200387],
            [1.0, 0.99999902, 0.40440860],
            [1.0, 1.0, 0.81733436],
        ])
        assert p.shape == (3, 3)
        assert np.allclose(p, expected, rtol=1e-7, atol=1e-10)

    def test_prob_decreases_with_distance(self):
        d = np.array([0.05])
        r_near = np.array([0.1])
        r_far = np.array([5.0])
        rx = np.array([0.1])
        p_near = float(np.atleast_1d(
            self.model.get_prob(d=d, mag=6.5, r=r_near, rx=rx)).flat[0])
        p_far = float(np.atleast_1d(
            self.model.get_prob(d=d, mag=6.5, r=r_far, rx=rx)).flat[0])
        assert p_far <= p_near

    def test_prob_decreases_with_displacement(self):
        d = np.array([0.001, 0.01, 0.1, 1.0])
        r = np.array([0.5])
        rx = np.array([0.1])
        p = self.model.get_prob(d=d, mag=6.5, r=r, rx=rx)
        p_flat = np.atleast_1d(p).flatten()
        if p_flat.size == d.size:
            assert np.all(np.diff(p_flat) <= 1e-10)

    def test_complex_faulting(self):
        d = np.array([0.01])
        r = np.array([0.5])
        rx = np.array([0.1])
        p = self.model.get_prob(d=d, mag=6.5, r=r, rx=rx,
                                faulting="complex")
        assert 0.0 <= float(np.atleast_1d(p).flat[0]) <= 1.0

    def test_footwall_side(self):
        d = np.array([0.01])
        r = np.array([0.5])
        rx = np.array([-0.1])
        p = self.model.get_prob(d=d, mag=6.5, r=r, rx=rx)
        assert 0.0 <= float(np.atleast_1d(p).flat[0]) <= 1.0

    def test_invalid_method_raises(self):
        with pytest.raises(ValueError):
            self.model.get_prob(d=[0.1], mag=6.5, r=[0.5], rx=[0.1],
                                method="unknown")

    @pytest.mark.parametrize("kwargs", [
        {"version": "XX"},
        {"version": "AD", "completeness": "incomplete"},
        {"sigma_type": "unknown"},
        {"faulting": "unknown"},
        {"percentile": "95"},
    ])
    def test_invalid_options_raise(self, kwargs):
        base = {"d": [0.1], "mag": 6.5, "r": [0.5], "rx": [0.1]}
        base.update(kwargs)
        with pytest.raises(ValueError):
            self.model.get_prob(**base)

    def test_multi_site(self):
        d = np.array([0.01, 0.1])
        r = np.array([0.2, 1.0, 3.0])
        rx = np.array([0.1, 0.1, -0.1])
        p = self.model.get_prob(d=d, mag=6.5, r=r, rx=rx)
        p_arr = np.atleast_2d(p)
        assert p_arr.shape == (3, 2)
        assert np.all(p_arr >= 0) and np.all(p_arr <= 1)

    def test_legacy_ini_aliases_match_explicit_args(self):
        d = np.array([0.01, 0.1])
        r = np.array([0.5])
        rx = np.array([0.1])
        p_alias = np.atleast_1d(self.model.get_prob(
            d=d, mag=6.5, r=r, rx=rx,
            dataset="complete", use_revised_sigma=True, hw_fw="hw",
        ))
        p_explicit = np.atleast_1d(self.model.get_prob(
            d=d, mag=6.5, r=r, rx=rx,
            completeness="complete", sigma_type="recommended",
        ))
        assert np.allclose(p_alias, p_explicit, rtol=1e-12, atol=0.0)

    def test_gamma_a_override_changes_distribution(self):
        d = np.array([0.01, 0.1, 1.0])
        r = np.array([0.174])
        rx = np.array([0.1])
        p_default = np.atleast_1d(self.model.get_prob(d=d, mag=6.5, r=r, rx=rx))
        p_override = np.atleast_1d(self.model.get_prob(
            d=d, mag=6.5, r=r, rx=rx, gamma_a=2.5
        ))
        assert not np.allclose(p_default, p_override)


# =====================================================================
# TIER 3: HAZARD CURVE REFERENCE FROM FIGURE 6.1
# Reference: GIRS-2022-05, Section 6, Figure 6.1
# =====================================================================


class TestHazardCurveReference:
    """
    Fast reference checks for equations used by the GIRS-2022-05 Section 6
    demonstration case.

    Scenario:
      - Mw 7.5 reverse fault
      - Slip rate: 5 mm/yr
      - Fault dimensions: 100 km x 15 km
      - Stiff soil (VS30 > 600 m/s)
      - x/L = 0.5 (middle of fault)
      - Hanging wall conditions
      - Simple fault geometry

    The full 975-year return-period comparison to the Figure 6.1 hazard curve
    is a Monte Carlo benchmark and is kept in ``test_moss2022_figure6_1.py``.
    """

    @pytest.mark.parametrize(
        "r_km, expected", [
            (0.0, 1.0),
            (0.1, 1.0),
            (0.25, 0.951229),
            (0.5, 0.548812),
            (1.0, 0.182684),
            (2.0, 0.020242),
            (3.0, 0.002243),
        ])
    def test_table_5_3_hw_pd0_reference_values(self, r_km, expected):
        """Eq. 5.5 / Table 5.3 hanging-wall P(d > 0) values."""
        ssr = Moss2022SecondarySR()
        assert float(ssr.get_prob(r=r_km, rx=0.1)) == pytest.approx(
            expected, abs=1e-6)

    @pytest.mark.parametrize(
        "r_km, expected", [
            (0.0, 1.0),
            (0.5, 0.449329),
            (1.0, 0.135335),
        ])
    def test_table_5_3_fw_pd0_reference_values(self, r_km, expected):
        """Eq. 5.5 / Table 5.3 footwall P(d > 0) values."""
        ssr = Moss2022SecondarySR()
        assert float(ssr.get_prob(r=r_km, rx=-0.1)) == pytest.approx(
            expected, abs=1e-6)

    @pytest.mark.parametrize(
        "r_km, expected", [
            (0.0, 0.43),
            (0.1, 0.413139),
            (0.5, 0.352054),
            (1.0, 0.288238),
            (3.0, 0.129514),
        ])
    def test_table_5_8_hw_simple_d_md_reference_values(self, r_km, expected):
        """Table 5.8 85th-percentile HW simple d/MD envelope values."""
        ec = ENVELOPE_85['simple']['hw']
        value = ec['c'] * math.exp(ec['d'] * r_km)
        assert value == pytest.approx(expected, abs=1e-6)

    @pytest.mark.parametrize(
        "r_km, expected", [
            (0.0, 0.68),
            (1.0, 0.597105),
        ])
    def test_table_5_8_fw_simple_d_md_reference_values(self, r_km, expected):
        """Table 5.8 85th-percentile FW simple d/MD envelope values."""
        ec = ENVELOPE_85['simple']['fw']
        value = ec['c'] * math.exp(ec['d'] * r_km)
        assert value == pytest.approx(expected, abs=1e-6)
