# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2026 GEM Foundation
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
import pickle


def configuration_key(options, excluded):
    """Make a hashable key while preserving the order of model options."""
    return pickle.dumps(tuple((name, value) for name, value in options
                              if name not in excluded))


def branch_key(compute, *varying):
    """Define the key of branches that differ only in the given options."""
    excluded = {'weight', *varying}
    # Subclasses with their own compute implementation must opt in again.
    @property
    def key(gsim):
        if type(gsim).compute is compute:
            return (type(gsim), configuration_key(
                sorted(gsim.kwargs.items()), excluded))
    return key


def sigma_mu_key(compute, *excluded):
    """Group models with a common backbone and different sigma_mu shifts."""
    return branch_key(compute, 'sigma_mu_epsilon', *excluded)


def compute_without_shift(gsim, ctx, imts, mean, sig, tau, phi, gra_mon=None):
    """Compute the shared predictions and pass the context to the shift."""
    gsim.compute(ctx, imts, mean, sig, tau, phi, apply_shift=False)
    return ctx
