# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2025, GEM Foundation
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

import pandas
from openquake.baselib import sap, writers
from openquake.commonlib import readinput
from openquake.hazardlib.geo.utils import geolocate


def main(lon_lat_csv, assoc_csv):
    df = pandas.read_csv(lon_lat_csv).sort_values(['lon', 'lat'])
    models = geolocate(df[['lon', 'lat']], readinput.read_mosaic_df(buffer=0))
    writers.write_csv(assoc_csv, zip(df.lon, df.lat, models),
                      ',', '%8.3f', ['lon', 'lat', 'model'])


if __name__ == '__main__':
    sap.run(main)
