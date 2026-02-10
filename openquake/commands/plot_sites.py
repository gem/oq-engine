# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2026 GEM Foundation
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

from openquake.baselib import hdf5, sap
from openquake.hazardlib.geo.utils import geolocate_with_index
from openquake.hazardlib.geo.spatial_index import get_mosaic_spatial_index
from openquake.calculators.postproc.plots import add_borders, add_region_labels


def get_lon_lat(csvfile):
    lon = 'Longitude' if 'Longitude' in csvfile.fields else 'lon'
    lat = 'Latitude' if 'Latitude' in csvfile.fields else 'lat'
    return csvfile.read_df().rename(columns={lon: 'lon', lat: 'lat'})


def main(files_csv):
    """
    Plot the sites contained in the file
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as p

    csvfiles = hdf5.sniff(files_csv)
    dfs = [get_lon_lat(csvfile) for csvfile in csvfiles]

    fig = p.figure()
    ax = fig.add_subplot(111)
    ax.grid(True)
    markersize = 5
    mosaic_spatial_index = get_mosaic_spatial_index()
    for csvfile, df in zip(csvfiles, dfs):
        models = geolocate_with_index(df[['lon', 'lat']], mosaic_spatial_index)
        p.scatter(df.lon, df.lat, marker='o',
                  label=csvfile.fname, s=markersize)
        for model, lon, lat in zip(models, df.lon, df.lat):
            ax.annotate(model, (lon, lat))
        # for model, id, lon, lat in zip(models, df.ID, df.lon, df.lat):
        #     ax.annotate(model + str(id), (lon, lat))
    add_borders(ax, spatial_index=mosaic_spatial_index)
    add_region_labels(ax, spatial_index=mosaic_spatial_index)
    p.show()
    return p


main.files_csv = dict(help='a path to a CSV file with lon, lat fields',
                      nargs='+')

if __name__ == '__main__':
    sap.run(main)
