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

r"""
Probabilistic Fault Displacement (PFD) rate kernel.

The kernel is the engine-idiomatic port of oq-pfdha's
``calc/hazard.py::_compute_rupture_contribution`` plus its
``calc/location_weight.py``. It computes, per rupture and per site, the
annual exceedance rates of fault displacement:

.. math::

    \lambda_{\mathrm{principal}} = \mathrm{rate} \cdot P_{sr} \cdot P_{fd,\mathrm{primary}} \cdot W_p(r)
    \lambda_{\mathrm{distributed}} = \mathrm{rate} \cdot P_{sr} \cdot P_{dist,\mathrm{combined}}(r) \cdot G(r)

``P_sr = P(SR | m)`` is the ONLY probability that the rupture breaks the
surface, given by the primary surface-rupture model of the logic-tree
branch. In particular the ``rate`` of a floating rupture is the rate of its
magnitude marginalized over the down-dip float positions
(:func:`collapse_downdip`): the fraction of positions that touch the surface
depends on the mesh and must not act as a second surface-rupture
probability on top of ``P_sr``.

``W_p(r)`` is the rupture-location weight (see :func:`location_weight`) and
the distributed weight is its complement ``G = 1 - W_p`` on both paths:

* ``r_sigma_km == 0`` -- boxcar ``W_p = 1{|r| <= r_threshold_km}``: inside
  the half-width only principal, outside only distributed (Youngs 2003 /
  Takao 2013 either/or);
* ``r_sigma_km > 0``  -- Petersen et al. (2011) pinned, +/-2-sigma Gaussian
  ``W_p``: each site blends ``W_p`` x principal + ``(1 - W_p)`` x
  distributed; on the trace ``G = 0``, beyond 2 sigma ``G = 1``.

Inside a distributed model's own declared near-trace exclusion
(``APPLICABILITY_RANGE['r_min_km']``, e.g. 5 m for Visini et al. 2025) the
regression is undefined and the distributed term is set to zero.

An aggregate-definition primary FD model (Sarmiento et al. 2025 Table 1, the
class choice IS the definition) already includes the distributed
contribution: ``lambda_total = rate * P_sr * P_fd_aggregate * W_p`` flows
through the principal bucket and the distributed bucket stays zero.

The kernel deliberately does NOT call ``get_mean_stds``/``get_poes``. The PFD models yield exceedance probabilities directly.
The calculator wraps the returned rate arrays into the engine's ``MapArray``
and reuses all downstream stats/export machinery.

The pure functions here take objects exposing the adapter protocol
(:class:`openquake.pfd.adapter.PFDModelAdapter`: ``compute_primary_sr``,
``compute_primary_fd``, ``compute_secondary_sr``, ``compute_secondary_fd``,
each ``(ctx, ...) -> array``), keyed by the slot names
``primary_sr`` / ``primary_fd`` / ``secondary_sr`` / ``secondary_fd``. The
Visini rank-2 combined pipeline is not part of this kernel
yet; a Visini chain is routed through the generic SR x FD path until then.
"""
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

import numpy as np

from openquake.hazardlib.codes import (
    SIMPLE_FAULT, COMPLEX_FAULT, KITE_FAULT)

#: default Monte-Carlo / epistemic reduction; the mean is oq-pfdha's
#: default and is exact inside the rate sum (expectation is linear), so
#: the engine reproduces oq-pfdha's mean hazard curve. The median is a
#: legacy central-estimate heuristic that deviates at high displacement
#: levels.
DEFAULT_RED_CFG = {'method': 'mean'}


#: codes of the source typologies whose ruptures are floated over the fault
#: surface (simple, complex and kite fault sources). The ruptures of the
#: other typologies are given one by one and are never collapsed.
FLOATING_CODES = (SIMPLE_FAULT, COMPLEX_FAULT, KITE_FAULT)


def collapse_downdip(ruptures, depth_tolerance_km: float):
    """
    Marginalize the down-dip float of the ruptures of a floating source.

    A floating source spreads the rate of each magnitude over all the
    positions of the rupture on the fault surface, along strike and down
    dip. Whether a rupture of that magnitude breaks the surface is the
    business of the primary surface-rupture model alone, ``P(SR | m)``:
    the fraction of float positions that happen to touch the surface is a
    property of the mesh, not a probability. So the rates of each magnitude
    are summed over the down-dip positions and carried by the positions
    whose top edge is at the surface, which provide the geometry:

        sum of the returned rates of magnitude m == rate of magnitude m

    for any mesh spacing. The surface positions keep their relative rates,
    i.e. the along-strike distribution of the float is untouched.

    :param ruptures: all the ruptures of ONE floating source, each with
        ``mag``, ``occurrence_rate`` and ``surface.get_top_edge_depth()``.
        Their ``occurrence_rate`` is modified in place.
    :param depth_tolerance_km: a top edge within this depth is at the surface
    :returns: ``(surface_ruptures, blind)`` where ``blind`` maps the
        magnitudes with no position at the surface to their (dropped) rate:
        the geometry declares them buried, so there is no trace to carry
        the hazard
    """
    by_mag = {}
    for rup in ruptures:
        by_mag.setdefault(rup.mag, []).append(rup)
    out, blind = [], {}
    for mag, rups in by_mag.items():
        total = sum(rup.occurrence_rate for rup in rups)
        surf = [rup for rup in rups
                if rup.surface.get_top_edge_depth() <= depth_tolerance_km]
        surf_rate = sum(rup.occurrence_rate for rup in surf)
        if surf_rate <= 0.:
            blind[mag] = total
            continue
        factor = total / surf_rate
        for rup in surf:
            rup.occurrence_rate *= factor
        out.extend(surf)
    return out, blind


def get_lower_depth(src, ruptures=()):
    """
    The depth (km) of the bottom of the fault of a source, i.e. its lower
    seismogenic depth, as declared in the source model: the bottom of the
    mesh is off by up to half the mesh spacing.

    :param src: a source
    :param ruptures: the ruptures of a floating source, used if the source
        declares no depth (kite faults)
    :returns: the depth, or None if nothing is declared and there are no
        ruptures; the bottom of each rupture is used then
    """
    depth = getattr(src, 'lower_seismogenic_depth', None)
    if depth is not None:  # simple fault
        return float(depth)
    edges = getattr(src, 'edges', None)
    if edges:  # complex fault
        return float(max(point.depth for edge in edges for point in edge))
    # characteristic fault with a simple or complex geometry
    depth = getattr(getattr(src, 'surface', None), 'original_zbot', None)
    if depth is not None:
        return float(depth)
    if len(ruptures):
        return float(
            max(np.nanmax(rup.surface.mesh.depths) for rup in ruptures))


class SurfaceRuptures(object):
    """
    A floating source seen by the PFD calculator: the same source, except
    that :meth:`iter_ruptures` yields only the positions at the surface,
    carrying the rate of all the down-dip positions of their magnitude
    (see :func:`collapse_downdip`). It is meant to be passed to
    :meth:`openquake.hazardlib.contexts.ContextMaker.get_ctxs` in place of
    the source, so that no context is built for the buried positions.

    After :meth:`iter_ruptures` has run, ``lower_depth`` is the lower
    seismogenic depth of the source and ``blind`` the magnitudes that never
    reach the surface (magnitude -> dropped rate).
    """
    def __init__(self, src, depth_tolerance_km):
        self.src = src
        self.depth_tolerance_km = depth_tolerance_km
        self.lower_depth = None
        self.blind = {}

    def __getattr__(self, name):
        if name == 'src':  # not initialized yet (i.e. when unpickling)
            raise AttributeError(name)
        return getattr(self.src, name)

    def iter_ruptures(self, **kwargs):
        allrups = list(self.src.iter_ruptures(**kwargs))
        self.lower_depth = get_lower_depth(self.src, allrups)
        rups, self.blind = collapse_downdip(allrups, self.depth_tolerance_km)
        if self.src.code == SIMPLE_FAULT:
            # use the declared dip, not the one recomputed from the mesh,
            # as for the characteristic faults
            for rup in rups:
                rup.surface.original_dip = float(self.src.dip)
        return iter(rups)


def location_weight(r, r_threshold_km: float, r_sigma_km: float,
                    r_sigma_truncation: float = 2.0) -> np.ndarray:
    """
    Principal-contribution rupture-location weight ``W_p(r)``.

    Two mutually exclusive paths (Petersen et al. 2011, Tables 2-3 and
    p. 819; see the oq-pfdha design notes on rupture-location uncertainty):

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


def _inside_declared_exclusion(adapter, ctx) -> Optional[np.ndarray]:
    """
    Sites closer to the rupture than the distributed model's own published
    near-trace exclusion, in the model's own distance metric.

    A regression fitted only beyond some minimum distance predicts nothing
    inside it: Visini et al. (2025) exclude data within 5 m of the
    principal rupture because such scarps cannot be told apart from
    principal faulting (pp. 11, 20), and their ln(s) predictor is unbounded
    as s -> 0. The complementary weight suppresses the distributed term on
    the trace but not just off it, so the exclusion is enforced here.

    :returns: boolean mask over the context sites, or ``None`` when the
        model declares no ``r_min_km``
    """
    rng = getattr(adapter.model, 'APPLICABILITY_RANGE', None)
    if not rng or 'r_min_km' not in rng:
        return None
    metrics = getattr(adapter, '_ctx_metrics', None)
    r = metrics(ctx)[0] if metrics is not None else ctx.rtor
    return np.abs(np.asarray(r, dtype=np.float64)) < float(rng['r_min_km'])


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
    :param r_sigma_km: mapping-error sigma; 0 selects the boxcar ``W_p``,
        > 0 the pinned Gaussian ``W_p`` (``G = 1 - W_p`` on both paths)
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

    if 'secondary_combined' in adapters:
        # combined distributed pipeline (Visini et al. 2025 A/B/C)
        p_dist = np.asarray(
            adapters['secondary_combined'].compute(ctx, imls, red_cfg),
            dtype=np.float64)
    else:
        if 'secondary_sr' in adapters:
            p_sr_sec = np.asarray(
                adapters['secondary_sr'].compute_secondary_sr(ctx, red_cfg),
                dtype=np.float64)
        else:
            p_sr_sec = np.zeros(n_ctx, dtype=np.float64)

        if 'secondary_fd' in adapters:
            p_fd_sec = np.asarray(
                adapters['secondary_fd'].compute_secondary_fd(
                    ctx, imls, red_cfg),
                dtype=np.float64)
        else:
            p_fd_sec = np.zeros((n_ctx, n_displ), dtype=np.float64)

        p_dist = p_sr_sec[:, np.newaxis] * p_fd_sec

    g = 1.0 - wp

    principal = rate * p_sr[:, np.newaxis] * p_fd_primary * wp[:, np.newaxis]
    distributed = rate * p_sr[:, np.newaxis] * p_dist * g[:, np.newaxis]
    if 'secondary_fd' in adapters:
        excl = _inside_declared_exclusion(adapters['secondary_fd'], ctx)
        if excl is not None and excl.any():
            distributed[excl] = 0.0
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
    Accumulate the PFD annual exceedance rates over a sequence of contexts.

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
