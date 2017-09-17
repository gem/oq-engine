# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017 GEM Foundation
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

from __future__ import print_function
import logging

from openquake.baselib import performance, sap, hdf5
from openquake.commonlib import datastore
from openquake.calculators.extract import extract as extract_


# the export is tested in the demos
@sap.Script
def extract(what, calc_id=-1):
    """
    Extract an output from the datastore and save it into an .hdf5 file.
    """
    logging.basicConfig(level=logging.INFO)
    dstore = datastore.read(calc_id)
    parent_id = dstore['oqparam'].hazard_calculation_id
    if parent_id:
        dstore.parent = datastore.read(parent_id)
    with performance.Monitor('extract', measuremem=True) as mon, dstore:
        dic = extract_(dstore, what)
        if not hasattr(dic, 'keys'):
            dic = {dic.__class__.__name__: dic}
        fname = '%s_%d.hdf5' % (what, dstore.calc_id)
        hdf5.save(fname, dic)
        print('Saved', fname)
    if mon.duration > 1:
        print(mon)


extract.arg('what', 'string specifying what to export')
extract.arg('calc_id', 'number of the calculation', type=int)
