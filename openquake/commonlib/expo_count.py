# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2025, GEM Foundation
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

from collections import Counter
from openquake.baselib import hdf5, sap
from openquake.hazardlib.geo.utils import hex6

def count_assets(expo_hdf5):
    """
    Count the number of assets per hexagon hex6 in exposure.hdf5
    """
    acc = Counter()
    with hdf5.File(expo_hdf5) as h5:
        for row in h5['assets/slice_by_hex6'][:]:
            acc[row['hex6'].decode('ascii')] += int(row['stop'] - row['start'])
    return [item for item in sorted(acc.items(), key=lambda i: (i[1], i[0]))]


def count_sites(expo_hdf5):
    """
    Count the number of assets per hexagon hex6 in exposure.hdf5
    """
    with hdf5.File(expo_hdf5) as h5:
        sm = h5['site_model'][:]
        acc = Counter(hex6(sm['lon'], sm['lat']))
    return [item for item in sorted(acc.items(), key=lambda i: (i[1], i[0]))]


def main(expo_hdf5):
    """
    Counts the assets and the sites per hexagon
    """
    print(count_assets(expo_hdf5)[-5:])
    print(count_sites(expo_hdf5)[-5:])
main.expo_hdf5 = 'Path to exposure.hdf5'


if __name__ == '__main__':
    sap.run(main)
