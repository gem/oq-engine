# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2025 GEM Foundation
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
import os
from openquake.baselib import general, performance, hdf5
from openquake.commonlib import logs
from openquake.calculators.extract import Extractor, WebExtractor


# `oq extract` is tested in the demos
def main(what,
         calc_id: int = -1,
         webapi=False,
         local=False,
         *,
         extract_dir='.'):
    """
    Extract an output from the datastore and save it into an .hdf5 file.
    By default uses the WebAPI, otherwise the extraction is done locally.
    """
    with performance.Monitor('extract', measuremem=True) as mon:
        if local:
            if calc_id == -1:
                calc_id = logs.dbcmd('get_job', calc_id).id
            aw = WebExtractor(calc_id, 'http://localhost:8800', '').get(what)
        elif webapi:
            aw = WebExtractor(calc_id).get(what)
        else:
            aw = Extractor(calc_id).get(what)
        w = what.replace('/', '-').replace('?', '-')
        if hasattr(aw, 'array') and isinstance(aw.array, str):  # CSV string
            fname = os.path.join(extract_dir, '%s_%d.csv' % (w, calc_id))
            with open(fname, 'w', encoding='utf-8', newline='') as f:
                f.write(aw.array)
        else:  # save as npz
            fname = os.path.join(extract_dir, '%s_%d.npz' % (w, calc_id))
            hdf5.save_npz(aw, fname)
        print(f'Saved {general.humansize(os.path.getsize(fname))} in {fname}')
    if mon.duration > 1:
        print(mon)


main.what = 'string specifying what to extract'
main.calc_id = 'number of the calculation'
main.webapi = 'if passed, use the (possibly remote) WebAPI'
main.local = 'if passed, use the local WebAPI'
main.extract_dir = 'directory where to extract'
