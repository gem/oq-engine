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
Share the central computation across compatible branches of a GSIM.

Use :func:`shifted_compute` on the ``compute`` function that calculates
the central predictions.
A direct call computes the central predictions and applies the branch
adjustment. ContextMaker computes the central part once per group and
context slice, copies its output to each branch, then applies each
branch's adjustment. An override of ``compute`` opts in independently.

The grouping key snapshots the concrete class and constructor options
other than the options named by the decorator and the logic-tree weight.
Keep the GSIM configuration fixed after construction.
"""

from functools import partial

from decorator import decorate


# Pass the context to the adjustment if compute_func returns None.
def _compute_central(compute_func, gsim, ctx, imts, mean, sig, tau, phi):
    resolved = compute_func(gsim, ctx, imts, mean, sig, tau, phi)
    return ctx if resolved is None else resolved


# Build the direct-call method and attach the callbacks for grouped calls.
def _compute_adjusted(compute_func, apply_adjustment, central_key_excluded):
    def adjusted(func, gsim, ctx, imts, mean, sig, tau, phi):
        resolved = _compute_central(func, gsim, ctx, imts, mean, sig, tau, phi)
        return apply_adjustment(gsim, resolved, imts, mean, sig, tau, phi)

    compute = decorate(compute_func, adjusted)
    compute.compute_central = partial(_compute_central, compute_func)
    compute.apply_adjustment = apply_adjustment
    compute.central_key_excluded = central_key_excluded
    return compute


def shifted_compute(apply_adjustment, central_key_excluded):
    """
    Apply a branch adjustment after the central calculation.

    The original ``compute`` function (``compute_func``) fills the four
    output arrays and can return data for the adjustment. If it returns
    None, the adjustment receives the context.
    The adjustment takes ``(gsim, resolved, imts, mean, sig, tau, phi)``,
    modifies the outputs in place, and supplies the public return value
    of ``compute``. Shared data is local to a group and context slice.
    Treat it as read-only except for caching branch-independent work.

    ``central_key_excluded`` names the constructor options that may vary
    without changing the central calculation. It accepts a name or a
    collection of names. An instance can set ``share_central = False``
    during construction to disable sharing.
    """
    if isinstance(central_key_excluded, str):
        central_key_excluded = (central_key_excluded,)

    return partial(_compute_adjusted, apply_adjustment=apply_adjustment,
                   central_key_excluded=frozenset(central_key_excluded))
