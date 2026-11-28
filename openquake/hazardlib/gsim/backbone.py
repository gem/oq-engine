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
after ``gsim, ctx, imts, mean, sig, tau, phi`` (``adj`` instead of
``ctx`` when compute returns a value other than the context) name the
constructor options that vary by branch. MetaGSIM wraps ``compute`` to
preserve direct calls, while ContextMaker runs the original compute body
once per group. Keep the GSIM configuration fixed after construction.
"""

import inspect
import os
import pathlib

import numpy
import toml
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
    if (names[:1] != ('gsim',) or names[1] not in ('ctx', 'adj')
            or names[2:] != ('imts', 'mean', 'sig', 'tau', 'phi')):
        raise TypeError('apply_adjustment must start with gsim, ctx or '
                        'adj, imts, mean, sig, tau, phi')
    if any(param.kind not in (param.POSITIONAL_ONLY,
                              param.POSITIONAL_OR_KEYWORD)
           for param in params):
        raise TypeError('apply_adjustment arguments must be positional')
    return tuple(param.name for param in params[7:])


def adjusted_compute(compute_func, apply_adjustment):
    # Wrap direct calls with the adjustment of the class defining compute,
    # so a super().compute() call applies only the parent's adjustment.
    # ContextMaker calls the original method separately.
    names = adjustment_options(apply_adjustment)

    def adjusted(func, gsim, ctx, imts, mean, sig, tau, phi):
        adj = _compute_central(func, gsim, ctx, imts, mean, sig, tau,
                               phi)
        return apply_adjustment(
            gsim, adj, imts, mean, sig, tau, phi,
            *[gsim.kwargs[name] for name in names])

    return decorate(compute_func, adjusted)


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
    if type(value) is dict:
        return {_normalize_option(key): _normalize_option(item)
                for key, item in value.items()}
    if type(value) in (list, tuple):
        return type(value)(_normalize_option(item) for item in value)
    return value


def get_central_key(gsim):
    """
    Return a TOML representation of the central constructor options.

    Parameters following ``gsim, ctx, imts, mean, sig, tau, phi`` in the
    GSIM's ``apply_adjustment`` method are omitted from the key.
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
    apply_adjustment = getattr(type(gsim), 'apply_adjustment', None)
    if apply_adjustment is None:
        return None
    exclusions = adjustment_options(apply_adjustment)
    if not getattr(gsim, 'share_central', True):
        return None
    options = tuple((name, value) for name, value in gsim.kwargs.items()
                    if name != 'weight' and name not in exclusions)
    options = dict(options)
    name = type(gsim).__name__
    key = {'_gsim': name, name: fix_toml(options, basedir=None)}
    return toml.dumps(key).strip()
