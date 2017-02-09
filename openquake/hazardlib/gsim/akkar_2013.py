# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2017 GEM Foundation
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
Module exports :class:`AkkarEtAl2013`.
"""
from __future__ import division

import warnings
from openquake.hazardlib.gsim.akkar_2014 import AkkarEtAlRjb2014

class AkkarEtAl2013(AkkarEtAlRjb2014):
    """
    To ensure backwards compatibility with existing seismic hazard models,
    the call AkkarEtAl2013 is retained as legacy. The AkkarEtAl2013 GMPE
    is now implemented as AkkarEtAlRjb2014
    """
    deprecated = True
