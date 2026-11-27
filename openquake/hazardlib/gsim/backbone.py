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
import toml

from openquake.hazardlib.gsim.base import fix_toml


def configuration_key(options, excluded):
    """
    Make a key from the TOML representation of the model options, i.e.
    the same representation used to compare and hash the GSIMs; it
    cannot fail, since every GSIM is converted to TOML when it is built.
    """
    selected = {name: value for name, value in sorted(options.items())
                if name not in excluded}
    return toml.dumps(fix_toml(selected))


def branch_key(compute, *varying):
    """Build a constructor hook for branches that differ in these options."""
    excluded = {'weight', *varying}
    # Subclasses with their own compute implementation must opt in again.
    def key(gsim):
        if type(gsim).compute is compute:
            return type(gsim), configuration_key(gsim.kwargs, excluded)
    return key


def sigma_mu_key(compute, *excluded):
    """Group models with a common backbone and different sigma_mu shifts."""
    return branch_key(compute, 'sigma_mu_epsilon', *excluded)


def compute_without_shift(gsim, ctx, imts, mean, sig, tau, phi, gra_mon=None):
    """Compute the shared predictions and pass the context to the shift."""
    gsim.compute(ctx, imts, mean, sig, tau, phi, apply_shift=False)
    return ctx


def mean_shift_functions(apply_shift, *,
                         compute_central=compute_without_shift):
    """
    Pair shared computation with a callback that updates only the mean.
    Return the pair (compute_central, apply_branch) expected by
    ContextMaker; `compute_central` is keyword-only, to avoid confusing
    the order of the arguments with the order of the result.
    """
    def apply_branch(gsim, resolved, imts, outputs):
        return apply_shift(gsim, resolved, imts, outputs[0])
    return compute_central, apply_branch
