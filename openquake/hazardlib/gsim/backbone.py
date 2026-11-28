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

Decorate the central body of ``compute`` with :func:`shifted_compute`.
A direct call computes the central predictions and applies the branch
adjustment. ContextMaker computes the central part once per group and
context slice, copies its output to each branch, then applies each
branch's adjustment. An override of ``compute`` opts in independently.

The grouping key snapshots the concrete class and constructor options
other than the options named by the decorator and the logic-tree weight.
Keep the GSIM configuration fixed after construction.
"""

import inspect
from functools import wraps


def shifted_compute(apply_branch, options):
    """
    Apply a branch adjustment after the body of ``compute``.

    The body fills the four output arrays and can return data for the
    adjustment. If it returns None, the adjustment receives the context.
    The adjustment takes ``(gsim, resolved, imts, mean, sig, tau, phi)``,
    modifies the outputs in place, and supplies the public return value
    of ``compute``. Shared data is local to a group and context slice.
    Treat it as read-only except for caching branch-independent work.

    ``options`` is a name or collection of constructor option names used
    only by the adjustment. It can also be a function of the GSIM
    returning a collection of names or None to disable sharing for that
    instance. ContextMaker supplies its ray-tracing monitor to bodies
    that accept a ``gra_mon`` keyword.
    """
    if isinstance(options, str):
        options = (options,)

    def decorate(body):
        signature = inspect.signature(body)
        monitor = 'gra_mon' in signature.parameters

        def central(self, ctx, imts, mean, sig, tau, phi, gra_mon=None):
            args = (self, ctx, imts, mean, sig, tau, phi)
            if monitor and gra_mon is not None:
                resolved = body(*args, gra_mon=gra_mon)
            else:
                resolved = body(*args)
            return ctx if resolved is None else resolved

        @wraps(body)
        def compute(self, *args, **kwargs):
            gra_mon = kwargs.pop('gra_mon', None) if monitor else None
            if kwargs or len(args) != 6:
                args = signature.bind(self, *args, **kwargs).args[1:]
            resolved = central(self, *args, gra_mon=gra_mon)
            return apply_branch(self, resolved, *args[1:])

        compute.branch_functions = central, apply_branch
        compute.branch_options = options
        return compute

    return decorate
