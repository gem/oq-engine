#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2019 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import numpy
from openquake.baselib import sap, performance
from openquake.hazardlib.shakemap import download_array


@sap.script
def download_shakemap(id):
    """
    Example of usage: utils/shakemap usp000fjta
    """
    with performance.Monitor('shakemap', measuremem=True) as mon:
        dest = '%s.npy' % id
        numpy.save(dest, download_array(id))
    print(mon)
    print('Saved %s' % dest)


download_shakemap.arg('id', 'USGS Shakemap ID')
