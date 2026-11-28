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

A shifted GSIM class declares two methods. ``compute_adj(self, ctx, imts,
mean_stds)`` computes the central part, which is shared by the branches with
the same constructor options. It fills ``mean_stds``, the mean, sig, tau and
phi arrays, in place and returns a dictionary term -> array (None means an
empty dictionary).
``update_adj(gsim, ctx, adj, imts, mean_stds, *options)`` applies the
adjustment of a single branch, where ``options`` are the constructor options
that vary by branch and ``mean_stds`` holds the mean, sig, tau and phi
arrays. MetaGSIM generates ``compute`` from the two methods, so direct calls
apply the adjustment, while ContextMaker runs compute_adj once per group.
Keep the GSIM configuration fixed after construction.
"""

import inspect
import os
import pathlib

import numpy
import toml


def central_adjustments(compute_adj, gsim, ctx, imts, mean_stds):
    """
    Returns the dictionary computed by compute_adj, which is empty when
    compute_adj returns None
    """
    result = compute_adj(gsim, ctx, imts, mean_stds)
    return {} if result is None else result


def apply_options(gsim, ctx, adj, imts, mean_stds, update_adj, names):
    """
    Applies update_adj, passing the values of the constructor options named
    by names (as returned by adjustment_options) from kwargs
    """
    values = [gsim.kwargs[name] for name in names]
    update_adj(gsim, ctx, adj, imts, mean_stds, *values)


def adjustment_options(update_adj):
    # Extra callback arguments explicitly list branch-varying options.
    params = list(inspect.signature(update_adj).parameters.values())
    names = tuple(param.name for param in params[:5])
    if names != ('gsim', 'ctx', 'adj', 'imts', 'mean_stds'):
        raise TypeError('update_adj must start with gsim, ctx, adj, imts, '
                        'mean_stds')
    if any(param.kind not in (param.POSITIONAL_ONLY,
                              param.POSITIONAL_OR_KEYWORD)
           for param in params):
        raise TypeError('update_adj arguments must be positional')
    return tuple(param.name for param in params[5:])


def generate_compute(compute_adj, update_adj):
    """
    Returns the compute method made of the central computation followed by
    the adjustment. The two functions are bound here, at class creation, so
    that a super().compute() call applies only the parent's adjustment.
    """
    names = adjustment_options(update_adj)

    def compute(self, ctx: numpy.recarray, imts, mean, sig, tau, phi):
        mean_stds = (mean, sig, tau, phi)
        adj = central_adjustments(compute_adj, self, ctx, imts, mean_stds)
        apply_options(self, ctx, adj, imts, mean_stds, update_adj, names)

    compute.__doc__ = ("Compute mean, sig, tau and phi: the central "
                       "computation followed by the adjustment")
    return compute


def fix_toml(v, basedir=''):
    """
    Convert paths and Python objects such as arrays and CoeffsTables
    for TOML serialization.

    Keep paths inside ``basedir`` relative to it. Other absolute paths
    are serialized using their basename. With ``basedir=None``, preserve
    absolute paths.
    """
    if isinstance(v, str) and pathlib.PurePath(v).is_absolute():
        path = pathlib.PurePath(os.path.normpath(v))
        if basedir is None:
            return path.as_posix()
        if basedir and path.is_relative_to(basedir):
            return path.relative_to(basedir).as_posix()
        return path.name
    if isinstance(v, (numpy.float32, numpy.float64)):
        return float(v)
    elif isinstance(v, numpy.ndarray):
        return list(v)
    elif hasattr(v, 'to_dict'):
        return v.to_dict()
    elif hasattr(v, 'items'):
        return {k1: fix_toml(v1, basedir) for k1, v1 in v.items()}
    elif isinstance(v, list):
        return [fix_toml(x, basedir) for x in v]
    return v


# Convert filenames and NumPy values to their Python equivalents.
def _normalize_option(value):
    if isinstance(value, pathlib.PurePath):
        return os.fspath(value)
    if isinstance(value, numpy.ndarray):
        return _normalize_option(value.tolist())
    if isinstance(value, numpy.generic):
        return value.item()
    # TOML tables are dict subclasses which cannot be pickled
    if isinstance(value, dict):
        return {_normalize_option(key): _normalize_option(item)
                for key, item in value.items()}
    if type(value) in (list, tuple):
        return type(value)(_normalize_option(item) for item in value)
    return value


def get_central_key(gsim):
    """
    Return a TOML representation of the central constructor options.

    Parameters following ``gsim, ctx, adj, imts, mean_stds`` in the
    GSIM's ``update_adj`` method are omitted from the key.
    Constructor options are assumed to stay fixed after instantiation.
    The key is None for an ordinary compute method or a GSIM instance
    that disables sharing.

    >>> from openquake.hazardlib.gsim.kotha_2020 import KothaEtAl2020ESHM20
    >>> low = KothaEtAl2020ESHM20(sigma_mu_epsilon=-1.35563)
    >>> high = KothaEtAl2020ESHM20(sigma_mu_epsilon=1.35563)
    >>> get_central_key(low) == get_central_key(high)
    True
    >>> print(get_central_key(
    ...     KothaEtAl2020ESHM20(c3_epsilon=1.732051)))
    _gsim = "KothaEtAl2020ESHM20"
    <BLANKLINE>
    [KothaEtAl2020ESHM20]
    c3_epsilon = 1.732051
    """
    update_adj = getattr(type(gsim), 'update_adj', None)
    if update_adj is None:
        return None
    exclusions = adjustment_options(update_adj)
    if not getattr(gsim, 'share_central', True):
        return None
    options = tuple((name, value) for name, value in gsim.kwargs.items()
                    if name != 'weight' and name not in exclusions)
    options = dict(options)
    name = type(gsim).__name__
    key = {'_gsim': name, name: fix_toml(options, basedir=None)}
    return toml.dumps(key).strip()
