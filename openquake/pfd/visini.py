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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Combined secondary (distributed) pipeline of Visini et al. (2025).

The generic PFD adapter multiplies a secondary SR probability by a
secondary FD probability. The Visini models do not work that way: they
sum three combinations (A/B/C) with ``P = 1 - prod(1 - P_i)`` and split
the site population by hanging-wall/footwall and near/far regimes. This
module ports oq-pfdha's ``VisiniSecondaryCalculator`` so the engine can
route the models declaring ``SECONDARY_PIPELINE = 'visini'``.

The reference (rank 1.5) trace distance used by combination B is not
available in the engine yet, so - like oq-pfdha when no traces are
configured - combination B falls back to the principal-trace distance.
"""
from typing import List

import numpy as np

from openquake.pfd.probability import _to_sites_x_displ


def choose_combinations(case: str) -> List[str]:
    """
    Map a Visini case label to the active combinations.

    case1 -> ['A', 'B', 'C']; case2 -> ['A', 'B']; case3 -> ['A']
    """
    table = {"case1": ["A", "B", "C"], "case2": ["A", "B"], "case3": ["A"]}
    c = str(case).lower()
    if c not in table:
        raise ValueError(f'Unknown Visini case: {case}')
    return table[c]


def combine_probabilities(probs: List[np.ndarray]) -> np.ndarray:
    """
    Element-wise ``P = 1 - prod_i (1 - P_i)`` over ``(n_sites, n_displ)``.
    """
    if not probs:
        raise ValueError('No probability matrices provided.')
    out = probs[0]
    for p in probs[1:]:
        out = 1.0 - (1.0 - out) * (1.0 - p)
    return out


class VisiniSecondaryCalculator(object):
    """
    Compute the combined distributed contribution for one rupture.

    :param sr_model: a :class:`Visini2025SecondarySR` instance
    :param fd_model: a :class:`Visini2025SecondaryFD` instance
    :param case_label: Visini case ('case1' | 'case2' | 'case3')
    :param pixel_size: across-strike site cell width (m)
    :param near_far_threshold_km: near/far regime threshold (km)
    """

    def __init__(self, sr_model, fd_model, case_label='case1',
                 pixel_size=100, along_strike_width=None,
                 near_far_threshold_km=0.2, segment_sampling='truncated',
                 distribution_type='uniform'):
        self.sr_model = sr_model
        self.fd_model = fd_model
        self.combos = choose_combinations(case_label)
        self.pixel_size = int(pixel_size)
        self.along_strike_width = (
            float(along_strike_width) if along_strike_width is not None
            else float(pixel_size))
        self.near_far_threshold_km = float(near_far_threshold_km)
        self.segment_sampling = segment_sampling
        self.distribution_type = distribution_type

    def _style(self, ctx):
        for model in (self.sr_model, self.fd_model):
            style = getattr(model, 'style', None)
            if style is not None:
                return style
        style_arr = getattr(ctx, 'style', None)
        if style_arr is not None:
            return style_arr[0]
        from openquake.pfd.adapter import style_from_rake
        return style_from_rake(ctx.rake[0])

    def compute(self, ctx, imls, red_cfg):
        """
        :returns: the distributed probability matrix ``(n_sites, n_displ)``
        """
        imls = np.asarray(imls, dtype=float)
        r = np.atleast_1d(np.asarray(ctx.rtor, dtype=float))
        rx = np.atleast_1d(np.asarray(ctx.rx, dtype=float))
        length = np.atleast_1d(np.asarray(ctx.length, dtype=float))
        x_l = np.atleast_1d(np.asarray(ctx.x_l, dtype=float))
        dip = np.atleast_1d(np.asarray(ctx.dip, dtype=float))
        n_sites = len(r)
        n_displ = len(imls)

        mag = float(np.atleast_1d(ctx.mag)[0])
        r_m = r * 1000.0
        rx_m = rx * 1000.0
        fault_length_m = float(length[0]) * 1000.0
        style = self._style(ctx)
        pixel_size = getattr(self.sr_model, 'pixel_size', None) or (
            self.pixel_size)

        near_far = np.where(
            r <= self.near_far_threshold_km, 'near', 'far')

        probs = []
        for comb in self.combos:
            if comb in ('A', 'B'):
                res = self.sr_model.calculate_rank2_total_probability_vectorized(
                    mag=mag, r_array=r_m, rx_array=rx_m, style=style,
                    across_strike_width=pixel_size, combination=comb,
                    fault_length=fault_length_m,
                    along_strike_width=self.along_strike_width,
                    near_far_array=near_far,
                    distribution_type=self.distribution_type,
                    segment_sampling=self.segment_sampling)
                p_sr = np.atleast_1d(res['P_total'])
            else:
                p_sr = np.atleast_1d(self.sr_model.get_prob(
                    mag=mag, r=r_m, rx=rx_m, style=style,
                    pixel_size=pixel_size, combination=comb))
            if p_sr.size == 1:
                p_sr = np.full(n_sites, float(p_sr[0]))

            fd_kwargs = {}
            if getattr(self.fd_model, 'style', None) is None:
                fd_kwargs['style'] = style
            fd = self.fd_model.get_prob(
                d=imls, mag=mag, s=r_m, rx=rx_m, X_L_ratio=x_l, dip=dip,
                combination=comb, **fd_kwargs)
            fd_mat = _to_sites_x_displ(fd, n_sites, n_displ, red_cfg)
            probs.append(p_sr.reshape(n_sites, 1) * fd_mat)
        return combine_probabilities(probs)
