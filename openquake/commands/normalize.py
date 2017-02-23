#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2017, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import print_function
import csv
from openquake.baselib import sap
from openquake.hazardlib import valid


@sap.Script
def normalize(file_csv, sites_csv):
    """
    Produce a good `sites_csv` file from a generic CSV with fields longitude
    and latitude, by truncating to 5 digits and discarding duplicate sites.
    """
    with open(file_csv) as f:
        reader = csv.reader(f)
        header = next(reader)
        for i, field in enumerate(header):
            col = field.lower()
            if col in ('lon', 'longitude'):
                lon_idx = i
            if col in ('lat', 'latitude'):
                lat_idx = i
        points = set()
        for row in reader:
            point = valid.lon_lat('%s %s' % (row[lon_idx], row[lat_idx]))
            points.add(point)
    with open(sites_csv, 'w') as f:
        for point in sorted(points):
            f.write('%s,%s\n' % point)


normalize.arg('file_csv', 'CSV file with lon and lat in the header')
normalize.arg('sites_csv', 'name of the normalized sites.csv file')
