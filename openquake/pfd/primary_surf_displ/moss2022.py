# moss2022.py
# -*- coding: utf-8 -*-
"""
Module :mod:`openquake.pfd.primary_surf_displ.moss2022` implements
Moss et al. (2022) primary surface fault displacement model for reverse faults.

References
----------
Moss, R., Thompson, S., Kuo, C.-H., Younesi, K., and Baumont, D. (2022).
Reverse Fault PFDHA. Report GIRS-2022-05 (Revised 1/17/2024).
DOI: 10.34948/N3F595
"""
import numpy as np
from scipy import stats
from openquake.pfd.primary_surf_displ.base import BasePrimarySurfDispl

# ── Table 4.4: MD(M) and AD(M) scaling ──────────────────────────────────
# Form: log10(D) = a + b*M; s = regression sigma; s_rec = recommended sigma
SCALING = {
    'MD': {
        'complete':   {'a': -2.50, 'b': 0.415, 's': 0.148, 's_rec': 0.20},
        'incomplete': {'a': -2.71, 'b': 0.354, 's': 0.305, 's_rec': 0.35},
        'all':        {'a': -2.73, 'b': 0.422, 's': 0.354, 's_rec': None},
    },
    'AD': {
        'complete':   {'a': -2.87, 'b': 0.416, 's': 0.133, 's_rec': 0.20},
        'all':        {'a': -2.98, 'b': 0.427, 's': 0.181, 's_rec': 0.25},
    },
}

# ── Figures 4.3–4.4: x/L-dependent gamma regression coefficients ────────
# a_shape = a1 * x_L + a2;  b_scale = b1 * x_L + b2
GAMMA_REGRESSION = {
    'MD': {'a1': 1.4244, 'a2': 1.856,  'b1': -0.0832, 'b2': 0.1994},
    'AD': {'a1': 4.2797, 'a2': 1.6216, 'b1': -0.5003, 'b2': 0.5133},
}

# ── Equations 4.2–4.3: global (x/L-independent) gamma parameters ────────
# CRITICAL: b is the SCALE parameter despite the rate notation in Eq. 4.1;
# verified by Mean(D/AD) = a*b = 2.54199 * 0.393391 ≈ 1.0
GAMMA_GLOBAL = {
    'AD': {'a': 2.54199, 'b': 0.393391},
    'MD': {'a': 2.11095, 'b': 0.180981},
}


class Moss2022PrimaryFD(BasePrimarySurfDispl):
    """
    Moss et al. (2022) principal surface fault displacement exceedance model
    for reverse faults.

    Uses gamma-distributed D/MD (or D/AD) ratios convolved with log-normal
    MD(M) (or AD(M)) scaling to compute P(D > d₀ | M, x/L).

    This class implements the GIRS-2022-05 report formulation of the Moss et
    al. reverse-fault principal displacement model. For the principal model,
    the AD/MD magnitude-scaling coefficients match the values reported in
    Moss et al. (2024) Table 3 for the implemented complete/all branches. The
    practical differences are that this class exposes report-specific options:
    ``gamma_mode='global'``, the incomplete MD subset, and the ``sigma_type``
    selector. Use Moss2024PrimaryFD with ``source='EQS'`` when benchmarking the
    Earthquake Spectra Table 2 normalized-displacement alpha/beta parameters.

    Reference: GIRS-2022-05 (Revised 1/17/2024). DOI: 10.34948/N3F595

    Model contract: DISPLACEMENT_DEFINITION = "principal",
    DISPLACEMENT_COMPONENT = "vertical" -- GIRS-2022-05 Section 4 regresses
    principal reverse-fault displacement (D/MD, D/AD) from vertical-offset
    measurements on the principal scarp; component per the reverse-fault
    convention summarised in Valentini et al. (2025, Rev. Geophys.) Table 4.
    """

    DISPLACEMENT_DEFINITION = "principal"
    DISPLACEMENT_COMPONENT = "vertical"

    def get_prob(self, d, X_L_ratio, mag,
                 version="MD", completeness="complete",
                 gamma_mode="regression", sigma_type="recommended",
                 **extras):
        """
        Parameters
        ----------
        d : float or array-like
            Target displacement(s) in metres.
        X_L_ratio : float or array-like
            Normalized along-strike position, range [0, 1].
        mag : float
            Moment magnitude (scalar).
        version : str
            ``'AD'`` or ``'MD'``.
        completeness : str
            ``'complete'``, ``'incomplete'`` (MD only), or ``'all'``.
        gamma_mode : str
            ``'regression'`` (x/L-dependent) or ``'global'`` (Eqs 4.2–4.3).
        sigma_type : str
            ``'recommended'`` (revised Table 4.4 sigma) or ``'regression'``.
        extras
            Legacy keyword aliases for older INI wiring:
            ``dataset`` → ``completeness``;
            ``use_revised_sigma`` (bool) → ``sigma_type`` ``recommended`` / ``regression``.

        Returns
        -------
        numpy.ndarray
            Exceedance probability, squeezed from (n_disp, n_sites).
        """
        if "dataset" in extras:
            completeness = extras.pop("dataset")
        if "use_revised_sigma" in extras:
            sigma_type = (
                "recommended" if extras.pop("use_revised_sigma") else "regression"
            )
        if extras:
            unexpected = ", ".join(sorted(extras))
            raise TypeError(
                f"Moss2022PrimaryFD.get_prob() got unexpected keyword arguments: {unexpected}"
            )

        ver = version.upper()
        if ver not in ('AD', 'MD'):
            raise ValueError(f"Invalid version '{version}'. Accept: AD, MD")

        comp = completeness.lower()
        valid_comp = ('complete', 'incomplete', 'all') if ver == 'MD' \
            else ('complete', 'all')
        if comp not in valid_comp:
            raise ValueError(
                f"Invalid completeness '{completeness}' for version '{ver}'. "
                f"Accept: {valid_comp}")

        gm = gamma_mode.lower()
        if gm not in ('regression', 'global'):
            raise ValueError(
                f"Invalid gamma_mode '{gamma_mode}'. Accept: regression, global")

        st = sigma_type.lower()
        if st not in ('recommended', 'regression'):
            raise ValueError(
                f"Invalid sigma_type '{sigma_type}'. "
                "Accept: recommended, regression")

        if not np.isscalar(mag):
            raise ValueError("mag must be a scalar")

        d_arr = np.atleast_1d(np.asarray(d, dtype=float))
        x_arr = np.atleast_1d(np.asarray(X_L_ratio, dtype=float))
        if (x_arr < 0).any() or (x_arr > 1).any():
            raise ValueError("X_L_ratio must be between 0 and 1")

        folded_x = np.minimum(x_arr, 1 - x_arr)

        # ── Gamma shape (α) and scale (β) ──
        if gm == 'regression':
            c = GAMMA_REGRESSION[ver]
            alpha = c['a1'] * folded_x + c['a2']
            beta = c['b1'] * folded_x + c['b2']
        else:
            g = GAMMA_GLOBAL[ver]
            alpha = np.full_like(folded_x, g['a'])
            beta = np.full_like(folded_x, g['b'])

        # ── Magnitude scaling  μ, σ ──
        sc = SCALING[ver][comp]
        mu = sc['a'] + sc['b'] * mag
        sigma = (sc['s_rec']
                 if (st == 'recommended' and sc['s_rec'] is not None)
                 else sc['s'])

        # ── Numerical integration over ε ∈ [−6, 6] ──
        dz = 0.1
        eps = np.arange(-6.0, 6.0 + dz / 2, dz)
        z = 10 ** (mu + eps * sigma)
        p_eps = stats.norm.pdf(eps)

        # (n_eps, n_disp, n_sites)
        y = d_arr[None, :, None] / z[:, None, None]
        cdf_mat = stats.gamma.cdf(
            y, a=alpha[None, None, :], scale=beta[None, None, :])

        if ver == 'MD':
            c1 = stats.gamma.cdf(
                1.0, a=alpha[None, None, :], scale=beta[None, None, :])
            cdf_mat = np.where(y > 1.0, 1.0, cdf_mat / c1)

        cdf = np.tensordot(p_eps, cdf_mat, axes=(0, 0)) * dz
        prob = 1.0 - cdf

        return prob.squeeze()
