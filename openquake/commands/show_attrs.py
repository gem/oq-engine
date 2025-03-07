# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
from openquake.commonlib import datastore
import h5py


def main(key, calc_id=-1):
    """
    Show the attributes of a HDF5 dataset in the datastore.
    """
    try:
        calc_id = int(calc_id)
    except ValueError:  # passed filename
        hdf5 = h5py.File(calc_id)
    else:
        hdf5 = datastore.read(calc_id).hdf5
    try:
        attrs = h5py.File.__getitem__(hdf5, key).attrs
    except KeyError:
        print('%r is not in %s' % (key, hdf5))
    else:
        if len(attrs) == 0:
            print('%s has no attributes' % key)
        for name, value in attrs.items():
            print(name, value)
    finally:
        hdf5.close()


main.key = 'key of the datastore'
main.calc_id = 'calculation ID or filename.hdf5'
