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
# OpenQuake is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Fault Displacement Hazard Analysis (FDHA) rate kernel (PR-6 of the oq-engine
integration plan, Workstream D).

The kernel is the engine-idiomatic port of oq-pfdha's
``calc/hazard.py::_compute_rupture_contribution`` plus its
``calc/location_weight.py``. It computes, per surface-rupturing rupture and
per site, the annual exceedance rates of fault displacement:

    lambda_principal   = rate * P_sr * P_fd_primary       * W_p(r)
    lambda_distributed = rate * P_sr * P_dist_combined(r) * G(r)

``W_p(r)`` is the rupture-location weight (see :func:`location_weight`); the
distributed weight ``G`` depends on the ``W_p`` path:

* ``r_sigma_km == 0`` -- boxcar ``W_p = 1{|r| <= r_threshold_km}`` and the
  COMPLEMENTARY split ``G = 1 - W_p`` (Youngs 2003 / Takao 2013 either/or);
* ``r_sigma_km > 0``  -- Petersen et al. (2011) pinned, +/-2-sigma Gaussian
  ``W_p`` and the ADDITIVE split ``G = 1`` (eq. 1 + eq. 2, "total hazard").

An aggregate-definition primary FD model (Sarmiento et al. 2025 Table 1, the
class choice IS the definition) already includes the distributed
contribution: ``lambda_total = rate * P_sr * P_fd_aggregate * W_p`` flows
through the principal bucket and the distributed bucket stays zero.

The kernel deliberately does NOT call ``get_mean_stds``/``get_poes``
(decision D12): the FDHA models yield exceedance probabilities directly.
The calculator wraps the returned rate arrays into the engine's ``MapArray``
and reuses all downstream stats/export machinery.

The pure functions here take objects exposing the adapter protocol
(:class:`openquake.pfd.adapter.LegacyModelAdapter`: ``compute_primary_sr``,
``compute_primary_fd``, ``compute_secondary_sr``, ``compute_secondary_fd``,
each ``(ctx, ...) -> array``), keyed by the slot names
``primary_sr`` / ``primary_fd`` / ``secondary_sr`` / ``secondary_fd``. The
Visini rank-2 combined pipeline (Workstream H) is not part of this kernel
yet; a Visini chain is routed through the generic SR x FD path until then.
"""
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

import numpy as np

#: default Monte-Carlo / epistemic reduction
DEFAULT_RED_CFG = {'method': 'median', 'q': 50}


def location_weight(r, r_threshold_km: float, r_sigma_km: float,
                    r_sigma_truncation: float = 2.0) -> np.ndarray:
    """
    Principal-contribution rupture-location weight ``W_p(r)``.

    Two mutually exclusive paths (Petersen et al. 2011, Tables 2-3 and
    p. 819; see oq-pfdha ``docs/design/rupture_location_uncertainty.md``):

    * ``r_sigma_km == 0``: the legacy boxcar ``1{|r| <= r_threshold_km}``;
    * ``r_sigma_km > 0``: Petersen's Gaussian mapping-error weight, pinned to
      1 on the trace and truncated beyond ``+/- r_sigma_truncation * sigma``,
      with ``r_threshold_km`` playing no role.

    :param r: across-strike distance(s) to the mapped trace, km (``ctx.rtor``)
    :param r_threshold_km: boxcar half-width ``h`` (sigma == 0 path only)
    :param r_sigma_km: two-sided mapping-error sigma (km); 0 selects the boxcar
    :param r_sigma_truncation: truncation ``n`` in ``+/-n*sigma`` for the
        Gaussian path (Petersen p. 819: n = 2)
    :returns: ``float64`` array with the shape of ``r``; ``W_p(0) == 1``
    """
    r = np.abs(np.asarray(r, dtype=np.float64))
    sigma = float(r_sigma_km)
    if sigma == 0.0:
        return (r <= float(r_threshold_km)).astype(np.float64)
    n = float(r_sigma_truncation)
    wp = np.exp(-(r * r) / (2.0 * sigma * sigma))
    return np.where(r > n * sigma, 0.0, wp)


def _definition(model):
    """The static DISPLACEMENT_DEFINITION of a model (or ``None``)."""
    return getattr(model, 'DISPLACEMENT_DEFINITION', None)


def calc_rupture_contribution(
        ctx,
        adapters: Mapping[str, Any],
        imls: np.ndarray,
        r_threshold_km: float,
        r_sigma_km: float,
        red_cfg: Optional[Dict[str, Any]] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Principal and distributed annual-rate contributions of one rupture.

    :param ctx: a rupture context with ``occurrence_rate``, ``rtor`` and
        (for the adapters) the usual rupture/site fields
    :param adapters: slot name -> adapter; missing slots contribute zero
        (primary SR defaults to 1, the "always surface-ruptures" assumption)
    :param imls: displacement levels (m), shape ``(D,)``
    :param r_threshold_km: boxcar half-width for the ``W_p`` sigma == 0 path
    :param r_sigma_km: mapping-error sigma; 0 selects the complementary split
    :param red_cfg: Monte-Carlo reduction config
    :returns: ``(principal, distributed)``, each ``(N, D)`` annual rates
    """
    red_cfg = DEFAULT_RED_CFG if red_cfg is None else red_cfg
    imls = np.asarray(imls, dtype=np.float64)
    n_ctx = len(ctx)
    n_displ = len(imls)
    rate = float(ctx.occurrence_rate[0])

    if 'primary_sr' in adapters:
        p_sr = np.asarray(
            adapters['primary_sr'].compute_primary_sr(ctx, red_cfg),
            dtype=np.float64)
    else:
        p_sr = np.ones(n_ctx, dtype=np.float64)

    if 'primary_fd' in adapters:
        p_fd_primary = np.asarray(
            adapters['primary_fd'].compute_primary_fd(ctx, imls, red_cfg),
            dtype=np.float64)
    else:
        p_fd_primary = np.zeros((n_ctx, n_displ), dtype=np.float64)

    wp = location_weight(ctx.rtor, r_threshold_km, r_sigma_km)

    # Aggregate-definition primary model: single bucket, no distributed term.
    if ('primary_fd' in adapters
            and _definition(adapters['primary_fd'].model) == 'aggregate'):
        principal = (rate * p_sr[:, np.newaxis] * p_fd_primary
                     * wp[:, np.newaxis])
        return principal, np.zeros((n_ctx, n_displ), dtype=np.float64)

    if 'secondary_sr' in adapters:
        p_sr_sec = np.asarray(
            adapters['secondary_sr'].compute_secondary_sr(ctx, red_cfg),
            dtype=np.float64)
    else:
        p_sr_sec = np.zeros(n_ctx, dtype=np.float64)

    if 'secondary_fd' in adapters:
        p_fd_sec = np.asarray(
            adapters['secondary_fd'].compute_secondary_fd(ctx, imls, red_cfg),
            dtype=np.float64)
    else:
        p_fd_sec = np.zeros((n_ctx, n_displ), dtype=np.float64)

    p_dist = p_sr_sec[:, np.newaxis] * p_fd_sec

    if float(r_sigma_km) == 0.0:
        g = 1.0 - wp           # complementary (legacy boxcar split)
    else:
        g = np.ones_like(wp)   # additive (Petersen eq. 1 + eq. 2)

    principal = rate * p_sr[:, np.newaxis] * p_fd_primary * wp[:, np.newaxis]
    distributed = rate * p_sr[:, np.newaxis] * p_dist * g[:, np.newaxis]
    return principal, distributed


def calc_rates(
        contexts: Sequence[Any],
        n_sites: int,
        adapters: Mapping[str, Any],
        imls: np.ndarray,
        r_threshold_km: float,
        r_sigma_km: float,
        red_cfg: Optional[Dict[str, Any]] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Accumulate the FDHA annual exceedance rates over a sequence of contexts.

    :returns: ``(rates, principal, distributed)``, each ``(n_sites, D)``;
        ``rates = principal + distributed``
    """
    imls = np.asarray(imls, dtype=np.float64)
    n_displ = len(imls)
    rates = np.zeros((n_sites, n_displ), dtype=np.float64)
    principal = np.zeros((n_sites, n_displ), dtype=np.float64)
    distributed = np.zeros((n_sites, n_displ), dtype=np.float64)
    for ctx in contexts:
        p, d = calc_rupture_contribution(
            ctx, adapters, imls, r_threshold_km, r_sigma_km, red_cfg)
        contrib = p + d
        sids = np.asarray(ctx.sids, dtype=np.int64)
        if len(sids) != contrib.shape[0]:
            raise ValueError(
                "context/contribution shape mismatch: %d sids vs %d rows"
                % (len(sids), contrib.shape[0]))
        np.add.at(rates, sids, contrib)
        np.add.at(principal, sids, p)
        np.add.at(distributed, sids, d)
    return rates, principal, distributed
