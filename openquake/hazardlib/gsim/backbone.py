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

"""Shared computation for GSIM branches with additive mean shifts."""
import math


# Check exact types before encoding an option as a Python literal.
def _check_key_option(v):
    kind = type(v)
    if kind in (type(None), bool, int, str, bytes):
        return
    if kind is float and math.isfinite(v):
        return
    if kind in (list, tuple):
        for value in v:
            _check_key_option(value)
    elif kind is dict:
        for key, value in v.items():
            _check_key_option(key)
            _check_key_option(value)
    else:
        raise TypeError(f'Unsupported key option {kind.__name__}')


def backbone_key(gsim, excluded=()):
    """
    Snapshot the model options used by a shared computation, omitting
    weight and any excluded options. Return None for unsupported options
    so the GSIM is computed independently.

    The EUR Shallow Default branches vary stress and attenuation.
    Excluding ``sigma_mu_epsilon`` groups branches at fixed attenuation.

    >>> from openquake.hazardlib.gsim.kotha_2020 import KothaEtAl2020ESHM20
    >>> low = KothaEtAl2020ESHM20(sigma_mu_epsilon=-1.355630)
    >>> high = KothaEtAl2020ESHM20(sigma_mu_epsilon=1.355630)
    >>> backbone_key(low) == backbone_key(high)
    False
    >>> excluded = ('sigma_mu_epsilon',)
    >>> low_key = backbone_key(low, excluded)
    >>> high_key = backbone_key(high, excluded)
    >>> low_key == high_key
    True
    >>> slow = KothaEtAl2020ESHM20(sigma_mu_epsilon=1.355630,
    ...                            c3_epsilon=1.732051)
    >>> slow_key = backbone_key(slow, excluded)
    >>> high_key == slow_key
    False
    >>> slow_key[1]
    (('c3_epsilon', '1.732051'),)
    """
    pairs = []
    try:
        for name, value in gsim.kwargs.items():
            if name == 'weight' or name in excluded:
                continue
            _check_key_option(value)
            pairs.append((name, repr(value)))
    except (TypeError, RecursionError):
        return None
    return type(gsim), tuple(pairs)


def wrapped_key(gsim, *inputs):
    """Identify the wrapped GSIM and any additional hashable inputs."""
    inner = backbone_key(gsim.gmpe)
    if inner is not None:
        return (type(gsim), inner, *inputs)


def branch_key(compute, *varying):
    """
    Build a constructor hook for branches that differ in these options.
    Assign it to ``make_central_key`` in the GSIM class to set the key at
    construction. The hook returns None for a different implementation
    of ``compute``.

    EUR's Craton branches use ``branch_key(compute, 'epsilon')`` to share
    the prediction across mean shifts at a fixed ``site_epsilon``.

    >>> from openquake.hazardlib.gsim.eshm20_craton import ESHM20Craton
    >>> key = branch_key(ESHM20Craton.compute, 'epsilon')
    >>> low = ESHM20Craton(epsilon=-1.355630, site_epsilon=-1.732051)
    >>> high = ESHM20Craton(epsilon=1.355630, site_epsilon=-1.732051)
    >>> key(low) == key(high) == low.central_key == high.central_key
    True
    >>> key(high)[1]
    (('site_epsilon', '-1.732051'),)
    """
    # Subclasses with their own compute implementation must opt in again.
    def key(gsim):
        if type(gsim).compute is compute:
            return backbone_key(gsim, varying)
    return key


def sigma_mu_key(compute, *excluded):
    """
    Build a branch key hook that excludes ``sigma_mu_epsilon`` and any
    additional options named in ``excluded``.

    These EUR Subduction Interface branches use the same attenuation and
    forearc/backarc taper, so their different stress shifts share a key.

    >>> from openquake.hazardlib.gsim.eshm20_bchydro import BCHydroESHM20SInter
    >>> key = sigma_mu_key(BCHydroESHM20SInter.compute)
    >>> taper = dict(faba_taper_model='SFunc', a=-100., b=100.)
    >>> low = BCHydroESHM20SInter(sigma_mu_epsilon=-1.355630, **taper)
    >>> high = BCHydroESHM20SInter(sigma_mu_epsilon=1.355630, **taper)
    >>> key(low) == key(high) == low.central_key == high.central_key
    True
    >>> key(high)[1]
    (('faba_taper_model', "'SFunc'"), ('a', '-100.0'), ('b', '100.0'))
    """
    return branch_key(compute, 'sigma_mu_epsilon', *excluded)


def compute_without_shift(gsim, ctx, imts, mean, sig, tau, phi, gra_mon=None):
    """Compute the shared predictions and pass the context to the shift."""
    gsim.compute(ctx, imts, mean, sig, tau, phi, apply_shift=False)
    return ctx
