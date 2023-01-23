#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2023 GEM Foundation
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
"""
Determine the total number of ruptures in all the calculations in oqdata
"""
import glob
from openquake.commonlib.datastore import get_datadir, read
from openquake.calculators.views import text_table


def main(datadir):
    lst = []
    for fname in glob.glob(datadir + '/calc_*.hdf5'):
        try:
            dstore = read(fname)
        except OSError:  # already open
            continue
        with dstore:
            try:
                descr = dstore['oqparam'].description
            except (KeyError, AttributeError):  # not a calculation
                continue
            try:
                tot_ruptures = dstore['full_lt/sg_data']['totrup'].sum()
            except KeyError:
                tot_ruptures = 0
            else:
                lst.append((descr, tot_ruptures))
    print(text_table(lst, ['calculation', 'total number of ruptures']))


if __name__ == '__main__':
    main(get_datadir())
