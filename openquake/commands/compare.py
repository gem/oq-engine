#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2018, GEM Foundation

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
import sys
import numpy
from openquake.baselib import sap, datastore
from openquake.calculators import views
NSITES = 10


def get(dstore, what, imtls, sids):
    if what == 'hcurves':
        return dstore['hcurves/mean'].value[sids]
    elif what == 'hmaps':
        return dstore['hmaps/mean'].value[sids]  # shape (N, P * I)
    else:
        raise ValueError(what)


def getdata(what, calc_ids, sids):
    dstores = [datastore.read(calc_id) for calc_id in calc_ids]
    dstore = dstores[0]
    sitecol = dstore['sitecol']
    oq = dstore['oqparam']
    imtls = oq.imtls
    poes = oq.poes
    if not sids:
        if len(sitecol) > NSITES:  # sample at most NSITES
            sids = numpy.random.choice(len(sitecol), NSITES, replace=False)
        else:  # keep all sites
            sids = sitecol.sids
    arrays = [get(dstore, what, imtls, sids)]
    dstore.close()
    for dstore in dstores[1:]:
        oq = dstore['oqparam']
        numpy.testing.assert_equal(dstore['sitecol'].array, sitecol.array)
        numpy.testing.assert_equal(oq.imtls.array, imtls.array)
        numpy.testing.assert_equal(oq.poes, poes)
        arrays.append(get(dstore, what, imtls, sids))
        dstore.close()
    return sids, imtls, poes, arrays


@sap.Script
def compare(what, imt, calc_ids, site_ids):
    """
    Compare the hazard curves of two or more calculations
    """
    sids, imtls, poes, arrays = getdata(what, calc_ids, site_ids)
    try:
        levels = imtls[imt]
    except KeyError:
        sys.exit(
            '%s not found. The available IMTs are %s' % (imt, list(imtls)))
    imti = {imt: i for i, imt in enumerate(imtls)}
    if what == 'hcurves':
        header = ['site_id', 'calc_id'] + [str(lvl) for lvl in levels]
    else:
        header = ['site_id', 'calc_id'] + [str(poe) for poe in poes]
    rows = []
    for sid, array in zip(sids, arrays):
        for calc_id, pmap in zip(calc_ids, arrays):
            if what == 'hcurves':
                cols = array[imtls(imt)]
            else:
                cols = array[imti[imt]]
            rows.append([sid, calc_id] + list(cols))
    print(views.rst_table(rows, header))


compare.arg('what', 'hmaps or hcurves', choices={'hmaps', 'hcurves'})
compare.arg('imt', 'Intensity Measure Type to compare')
compare.arg('calc_ids', 'Calculation IDs', type=int, nargs='+')
compare.opt('site_ids', 'site IDs to compare', type=int, nargs='*')
