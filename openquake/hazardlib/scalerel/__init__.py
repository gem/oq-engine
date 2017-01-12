# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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
Package :mod:`openquake.hazardlib.scalerel` contains base classes and
implementations of magnitude-area and area-magnitude scaling relationships.
"""
import os
import inspect
import importlib
from collections import OrderedDict
from openquake.hazardlib.scalerel.base import BaseMSR, BaseASR, BaseMSRSigma, \
BaseASRSigma


from openquake.hazardlib.scalerel.ceus2011 import CEUS2011
from openquake.hazardlib.scalerel.peer import PeerMSR
from openquake.hazardlib.scalerel.point import PointMSR
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.scalerel.leonard2014 import (Leonard2014_SCR,
                                                      Leonard2014_Interplate)
from openquake.hazardlib.scalerel.strasser2010 import (StrasserInterface,
                                                       StrasserIntraslab)
from openquake.hazardlib.scalerel.wc1994_qcss import WC1994_QCSS




def _get_available_class(base_class):
    '''
    Return an ordered dictionary with the available classes in the
    scalerel submodule with classes that derives from `base_class`,
    keyed by class name.
    '''
    gsims = {}
    for fname in os.listdir(os.path.dirname(__file__)):
        if fname.endswith('.py'):
            modname, _ext = os.path.splitext(fname)
            mod = importlib.import_module(
                'openquake.hazardlib.scalerel.' + modname)
            for cls in mod.__dict__.values():
                if inspect.isclass(cls) and issubclass(cls, base_class) \
                        and cls != base_class \
                        and not inspect.isabstract(cls):
                    gsims[cls.__name__] = cls
    return OrderedDict((k, gsims[k]) for k in sorted(gsims))


def get_available_magnitude_scalerel():
    '''
    Return an ordered dictionary with the available Magnitude ScaleRel
    classes, keyed by class name.
    '''
    return _get_available_class(BaseMSR)

def get_available_sigma_magnitude_scalerel():
    '''
    Return an ordered dictionary with the available Sigma Magnitude
    ScaleRel classes, keyed by class name.
    '''
    return _get_available_class(BaseMSRSigma)


def get_available_area_scalerel():
    '''
    Return an ordered dictionary with the available Area ScaleRel
    classes, keyed by class name.
    '''
    return _get_available_class(BaseASR)


def get_available_sigma_area_scalerel():
    '''
    Return an ordered dictionary with the available Sigma Area ScaleRel
    classes, keyed by class name.
    '''
    return _get_available_class(BaseASRSigma)


def get_available_scalerel():
    '''
    Return an ordered dictionary with the available ScaleRel classes,
    keyed by class name.
    '''
    ret = get_available_area_scalerel()
    ret.update(get_available_magnitude_scalerel())

    return ret
