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
import struct


# Preserve type, value and order when taking a snapshot of model options.
def _freeze_option(value):
    kind = type(value)
    if kind in (type(None), bool, int, str, bytes):
        return kind, value
    if kind is float:
        return kind, struct.pack('!d', value)
    if kind is dict:
        return kind, tuple((_freeze_option(key), _freeze_option(item))
                           for key, item in value.items())
    if kind in (list, tuple):
        return kind, tuple(map(_freeze_option, value))
    raise TypeError(kind)


def configuration_key(gsim, excluded=()):
    """
    Snapshot the model options used by a shared computation. Return None
    for unsupported options so the GSIM is computed independently.
    """
    options = {name: value for name, value in gsim.kwargs.items()
               if name != 'weight' and name not in excluded}
    try:
        return type(gsim), _freeze_option(options)
    except (TypeError, RecursionError):
        return None


def branch_key(compute, *varying):
    """Build a constructor hook for branches that differ in these options."""
    # Subclasses with their own compute implementation must opt in again.
    def key(gsim):
        if type(gsim).compute is compute:
            return configuration_key(gsim, varying)
    return key


def sigma_mu_key(compute, *excluded):
    """Group models with a common backbone and different sigma_mu shifts."""
    return branch_key(compute, 'sigma_mu_epsilon', *excluded)


def compute_without_shift(gsim, ctx, imts, mean, sig, tau, phi, gra_mon=None):
    """Compute the shared predictions and pass the context to the shift."""
    gsim.compute(ctx, imts, mean, sig, tau, phi, apply_shift=False)
    return ctx
