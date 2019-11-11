# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2019 GEM Foundation
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
from openquake.baselib import performance, sap
from openquake.calculators.extract import Extractor, WebExtractor


# `oq extract` is tested in the demos
@sap.script
def extract(what, calc_id, webapi=True, local=False):
    """
    Extract an output from the datastore and save it into an .hdf5 file.
    By default uses the WebAPI, otherwise the extraction is done locally.
    """
    with performance.Monitor('extract', measuremem=True) as mon:
        if local:
            obj = WebExtractor(calc_id, 'http://localhost:8800', '').get(what)
        elif webapi:
            obj = WebExtractor(calc_id).get(what)
        else:
            obj = Extractor(calc_id).get(what)
        w = what.replace('/', '-').replace('?', '-')
        if not obj.shape:  # is a dictionary of arrays
            fname = '%s_%d.txt' % (w, calc_id)
            open(fname, 'w').write(obj.toml())
        else:  # a regular ArrayWrapper
            fname = '%s_%d.hdf5' % (w, calc_id)
            obj.save(fname)
        print('Saved', fname)
    if mon.duration > 1:
        print(mon)


extract.arg('what', 'string specifying what to export')
extract.arg('calc_id', 'number of the calculation', type=int)
extract.flg('webapi', 'if passed, use the (possibly remote) WebAPI')
extract.flg('local', 'if passed, use the local WebAPI')
