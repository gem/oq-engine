#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
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

from pprint import pprint
from openquake.commonlib import datastore, logictree, readinput
from openquake.calculators.extract import clusterize


def main(calc_id: int, *, k: int = 5):
    """
    Reduce the logic tree of the given calculation (classical, single-site,
    with return_periods or poes)
    """
    with datastore.read(calc_id) as dstore:
        oq = dstore['oqparam']
        hmaps = dstore['hmaps-rlzs'][0]
    full_lt = readinput.get_full_lt(oq)
    arr, cluster = clusterize(hmaps, full_lt.rlzs, k)
    pprint(logictree.reduce_full(full_lt, arr['branch_paths']))


main.calc_id = 'calculation ID'
main.k = 'number of realization clusters'
