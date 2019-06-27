# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2019 GEM Foundation
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

import os
import inspect
import importlib
from openquake.hmtk.faults.mfd.base import BaseMFDfromSlip


def get_available_mfds():
    '''
    Returns an ordered dictionary with the available GSIM classes
    keyed by class name
    '''
    mfds = {}
    for fname in os.listdir(os.path.dirname(__file__)):
        if fname.endswith('.py'):
            modname, _ext = os.path.splitext(fname)
            mod = importlib.import_module(
                'openquake.hmtk.faults.mfd.' + modname)
            for cls in mod.__dict__.values():
                if inspect.isclass(cls) and issubclass(cls, BaseMFDfromSlip):
                    mfds[cls.__name__] = cls
    return dict((k, mfds[k]) for k in sorted(mfds))
