#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2025 GEM Foundation
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

import shutil
import pandas
from openquake.hazardlib import valid
from openquake.hazardlib.geo.geodetic import fast_distance


def main(lon: valid.longitude, lat: valid.latitude, fname: str,
         maximum_distance: valid.positivefloat = 300.):
    """
    Reduce a CSV file with fields lon, lat to a shorter file around lon, lat
    """
    df = pandas.read_csv(fname)
    shutil.copy(fname, fname + '.bak')
    print('Copied the original file in %s.bak' % fname)
    dist = fast_distance(lon, lat, df.lon.to_numpy(), df.lat.to_numpy())
    red = df[dist <= maximum_distance]
    red.to_csv(fname, index=False, lineterminator='\r\n', na_rep='nan')
    print('Extracted %d lines out of %d' % (len(red), len(df)))


main.lon = 'longitude'
main.lat = 'latitude'
main.fname = 'path to a CSV file with fields lon, lat'
main.maximum_distance = 'maximum distance'
