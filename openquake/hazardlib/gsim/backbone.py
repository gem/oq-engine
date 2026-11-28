# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
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
Utilities for sharing central GSIM computations across branches.

Shifted GSIM classes declare an ``apply_adjustment`` method. Its arguments
after ``gsim, ctx, imts, mean, sig, tau, phi`` (``resolved`` instead of
``ctx`` when compute returns a value other than the context) name the
constructor options that vary by branch. MetaGSIM wraps ``compute`` to preserve direct
calls, while ContextMaker runs the original compute body once per group.
Keep the GSIM configuration fixed after construction.
"""

import inspect

from decorator import decorate


# Pass the context to the adjustment if compute_func returns None.
def _compute_central(compute_func, gsim, ctx, imts, mean, sig, tau, phi):
    result = compute_func(gsim, ctx, imts, mean, sig, tau, phi)
    return ctx if result is None else result


def adjustment_options(apply_adjustment):
    # Extra callback arguments explicitly list branch-varying options.
    params = list(inspect.signature(apply_adjustment).parameters.values())
    names = tuple(param.name for param in params[:7])
    # The second argument is the context, or the value returned by compute
    if (names[:1] != ('gsim',) or names[1] not in ('ctx', 'resolved')
            or names[2:] != ('imts', 'mean', 'sig', 'tau', 'phi')):
        raise TypeError('apply_adjustment must start with gsim, ctx or '
                        'resolved, imts, mean, sig, tau, phi')
    if any(param.kind not in (param.POSITIONAL_ONLY,
                              param.POSITIONAL_OR_KEYWORD)
           for param in params):
        raise TypeError('apply_adjustment arguments must be positional')
    return tuple(param.name for param in params[7:])


def adjustment_values(gsim, apply_adjustment):
    # Use initialized attributes when available, else constructor values.
    values = []
    for name in adjustment_options(apply_adjustment):
        if hasattr(gsim, name):
            values.append(getattr(gsim, name))
        else:
            values.append(gsim.kwargs.get(name))
    return values


def adjusted_compute(compute_func, apply_adjustment):
    # Wrap direct calls with the adjustment of the class defining compute,
    # so a super().compute() call applies only the parent's adjustment.
    # ContextMaker calls the original method separately.
    def adjusted(func, gsim, ctx, imts, mean, sig, tau, phi):
        resolved = _compute_central(func, gsim, ctx, imts, mean, sig, tau,
                                    phi)
        return apply_adjustment(
            gsim, resolved, imts, mean, sig, tau, phi,
            *adjustment_values(gsim, apply_adjustment))

    return decorate(compute_func, adjusted)
