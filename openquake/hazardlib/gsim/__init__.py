# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
Package :mod:`openquake.hazardlib.gsim` contains base and specific
implementations of ground shaking intensity models. See
:mod:`openquake.hazardlib.gsim.base`.
"""
import inspect
from openquake.baselib.general import import_all
from openquake.hazardlib.gsim.base import registry

import_all('openquake.hazardlib.gsim')


def get_available_gsims():
    '''
    Return an ordered dictionary with the available GSIM classes, keyed
    by class name.
    '''
    return dict(sorted(registry.items()))


def count_methods(cls):
    """
    Return the number of directly defined methods inside the class
    """
    return sum(1 for key, val in vars(cls).items()
               if inspect.isfunction(val) and key != '__init__')


def get_portable_gsims():
    '''
    Return an ordered dictionary with the portable GSIM classes, keyed
    by class name.
    '''
    portable = {}
    for cls in registry.values():
        if 'ctx' not in cls.compute.__annotations__:
            portable[cls.__name__] = cls
    return portable
