# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2026 Yen-Shin Chen, OGS
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Module :mod:`openquake.pfd.primary_surf_rup.youngs2003` implements
the model of Youngs et al. (2003) in :class:`Youngs2003PrimarySR`
"""

import numpy as np
from openquake.pfd.params import check_choice
from openquake.pfd.primary_surf_rup.base import BasePrimarySurfRup


def _canon_version(value):
    """Canonicalise a dataset name: case-, space- and punctuation-
    insensitive, with the documented aliases resolved."""
    s = str(value).strip().lower().replace("&", "and")
    for ch in " _-.()":
        s = s.replace(ch, "")
    return _VERSION_ALIASES.get(s, s)


#: Logistic coefficients (a, b) of Equation 4, from the Appendix of Youngs
#: et al. (2003), table "Coefficients for Equation 4 shown on Figure 4".
_COEFFS = {
    # Wells and Coppersmith (1993): 276 worldwide earthquakes, ALL slip types
    "WC93": (-12.51, 2.053),
    # Pezzopane and Dawson (1996) normal-faulting data sets
    "GreatBasin": (-16.02, 2.685),              # 32 earthquakes
    "NorthernBasinAndRange": (-18.71, 3.041),   # 47 earthquakes
    "ExtensionalCordillera": (-12.53, 1.921),   # 105 earthquakes
}

#: Number of earthquakes behind each regression, for provenance/reporting.
_DATASET_SIZE = {
    "WC93": 276, "GreatBasin": 32,
    "NorthernBasinAndRange": 47, "ExtensionalCordillera": 105,
}

_CANON_BY_LOWER = {k.lower(): k for k in _COEFFS}

#: Accepted spellings, including the pre-rename ``style`` vocabulary.
#: ``style='all'`` was the Wells and Coppersmith worldwide regression and
#: ``style='normal'`` the Great Basin one, so both map to their dataset.
_VERSION_ALIASES = {
    "wellsandcoppersmith1993": "wc93", "wellscoppersmith1993": "wc93",
    "wc1993": "wc93", "worldwide": "wc93", "all": "wc93",
    "gb": "greatbasin", "normal": "greatbasin",
    "nbr": "northernbasinandrange", "northernbasinrange":
        "northernbasinandrange", "basinandrange": "northernbasinandrange",
    "ec": "extensionalcordillera", "cordillera": "extensionalcordillera",
}

#: The dataset used when neither ``version`` nor ``style`` is given. This is
#: the historical default and is kept so existing inputs reproduce exactly;
#: it is NOT a recommendation (see the class docstring).
LEGACY_DEFAULT_VERSION = "WC93"


class Youngs2003PrimarySR(BasePrimarySurfRup):
    """
    Youngs et al. (2003) principal surface-rupture probability model.

    Logistic model of the probability of principal surface rupture as a
    function of magnitude (their Equation 4),
    ``P = exp(a + b*M) / (1 + exp(a + b*M))``. The model itself is one
    equation; what a branch selects is **which published data set the
    coefficients were fitted to**, via ``version``:

    ==========================  =======  ======  =====================
    version                           a       b  data set
    ==========================  =======  ======  =====================
    ``WC93``                    -12.51   2.053   276 worldwide earthquakes,
                                                 all slip types (Wells and
                                                 Coppersmith 1993)
    ``GreatBasin``              -16.02   2.685   32 Great Basin earthquakes
    ``NorthernBasinAndRange``   -18.71   3.041   47 northern Basin and Range
    ``ExtensionalCordillera``   -12.53   1.921   105 extensional cordillera
    ==========================  =======  ======  =====================

    The last three are the normal-faulting data sets of Pezzopane and
    Dawson (1996); all four are tabulated in the Appendix of Youngs et al.
    (2003) ("Coefficients for Equation 4 shown on Figure 4") and plotted in
    their Figure 4.

    .. warning::
       ``version="WC93"`` reproduces
       :class:`~openquake.pfd.primary_surf_rup.wells_coppersmith1993.
       WC1993PrimarySR` **exactly** - they are the same regression, so a
       branch set holding both carries one model under two names.

    .. note::
       **Pin the version.** A branch that specifies neither ``version``
       nor ``style`` does not get the class default: the calculator
       injects a ``style`` derived from the rupture rake
       (``calc/model_adapter.py:_resolve_style``), so the same XML yields
       ``GreatBasin`` on a normal-rake source, ``WC93`` if the branch says
       ``style = all``, and a configuration error on a reverse or
       strike-slip source (only 'all'/'normal' are accepted there). The
       coefficients therefore depend on the source model unless the branch
       pins ``version`` explicitly.

    The parameter was previously called ``style``, which was misleading:
    it never selected a faulting style, only a data set. ``style='all'``
    and ``style='normal'`` are still accepted and map to ``WC93`` and
    ``GreatBasin`` respectively, so existing inputs are unchanged.

    References
    ----------
    Youngs, R.R., et al. (2003). A methodology for probabilistic fault
    displacement hazard analysis (PFDHA). Earthquake Spectra, 19(1), 191-219.
    https://doi.org/10.1193/1.1542891
    Pezzopane, S.K., and Dawson, T.E. (1996). Fault displacement hazard: a
    summary of issues and information. In: Seismotectonic Framework and
    Characterization of Faulting at Yucca Mountain, Nevada, USGS
    Administrative Report, Chapter 4.
    Wells, D.L., and Coppersmith, K.J. (1993). Likelihood of surface rupture
    as a function of magnitude (abstract). SRL, 64(1), 54.
    """

    #: Accepted canonical dataset names.
    ACCEPTED_VERSIONS = frozenset(_COEFFS)

    def __init__(self, version=None, style=None):
        """
        :param version: data set whose coefficients to use - one of
            ``WC93``, ``GreatBasin``, ``NorthernBasinAndRange`` or
            ``ExtensionalCordillera`` (case- and space-insensitive, so
            ``"Great Basin"`` works). ``None`` defers to the ``get_prob``
            call, then to the legacy default ``WC93``.
        :param style: deprecated alias for ``version`` retained for
            backward compatibility; ``'all'`` maps to ``WC93`` and
            ``'normal'`` to ``GreatBasin``. If both are given, ``version``
            wins (see :meth:`get_prob` for the full precedence order).
        """
        super().__init__()
        # kept apart so an explicit branch ``version`` outranks a ``style``
        # injected at call time from the rupture rake (see get_prob)
        self._version = self._canon("version", version)
        self._style_version = self._canon("style", style)
        #: resolved data set (for manifests); ``None`` if neither was given
        self.version = self._version or self._style_version
        self.style = style

    @classmethod
    def _canon(cls, name, raw):
        """Validate one selector, returning its canonical name or None."""
        if raw is None:
            return None
        return _CANON_BY_LOWER[check_choice(
            cls.__name__, name, raw, {k.lower() for k in _COEFFS},
            canon=_canon_version)]

    def get_prob(self, mag, version=None, style=None):
        """
        :param mag: float or array-like, earthquake magnitude(s)
        :param version: data set selector for this call
        :param style: deprecated alias for ``version``
        :return: probability or array of probabilities

        Selection order, highest first: call-time ``version``, the
        constructor's ``version``, call-time ``style``, the constructor's
        ``style``, then the legacy default ``WC93``.

        The constructor's ``version`` deliberately outranks a call-time
        ``style`` because the calculator injects a rake-derived ``style``
        on *every* call (``calc/model_adapter.py:_resolve_style``). Without
        that ordering a branch pinning ``version = WC93`` on a normal-rake
        source would silently be served the Great Basin coefficients.
        """
        v = (self._canon("version", version)
             or self._version
             or self._canon("style", style)
             or self._style_version
             or LEGACY_DEFAULT_VERSION)
        a, b = _COEFFS[v]
        fx = a + b * np.asarray(mag, dtype=float)
        prob = np.exp(fx) / (1.0 + np.exp(fx))
        return prob.item() if prob.shape == () else prob
