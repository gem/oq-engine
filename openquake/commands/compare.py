# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2019 GEM Foundation
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
import sys
import collections
import numpy
from openquake.baselib import sap
from openquake.calculators.extract import Extractor
from openquake.calculators import views


def getdata(what, calc_ids, samplesites):
    extractors = [Extractor(calc_id) for calc_id in calc_ids]
    extractor = extractors[0]
    sitecol = extractor.get('sitecol')
    oq = extractor.oqparam
    imtls = oq.imtls
    poes = oq.poes
    if len(sitecol) > samplesites:
        numpy.random.seed(samplesites)
        sids = numpy.random.choice(len(sitecol), samplesites, replace=False)
    else:  # keep all sites
        sids = sitecol['sids']
    arrays = [extractor.get(what + '?kind=mean').mean[sids]]
    extractor.close()
    for extractor in extractors[1:]:
        oq = extractor.oqparam
        numpy.testing.assert_equal(
            extractor.get('sitecol').array, sitecol.array)
        if what == 'hcurves':
            numpy.testing.assert_equal(oq.imtls.array, imtls.array)
        elif what == 'hmaps':
            numpy.testing.assert_equal(oq.poes, poes)
        arrays.append(extractor.get(what + '?kind=mean').mean[sids])
        extractor.close()
    return sids, imtls, poes, numpy.array(arrays)  # shape (C, N, L)


def get_diff_idxs(array, rtol, atol):
    """
    Given an array with (C, N, L) values, being the first the reference value,
    compute the relative differences and discard the one below the tolerance.
    :returns: indices where there are sensible differences.
    """
    C, N, L = array.shape
    diff_idxs = set()  # indices of the sites with differences
    for c in range(1, C):
        for n in range(N):
            if not numpy.allclose(array[c, n], array[0, n], rtol, atol):
                diff_idxs.add(n)
    return numpy.fromiter(diff_idxs, int)


@sap.script
def compare(what, imt, calc_ids, files, samplesites=100, rtol=.1, atol=1E-4):
    """
    Compare the hazard curves or maps of two or more calculations
    """
    sids, imtls, poes, arrays = getdata(what, calc_ids, samplesites)
    try:
        levels = imtls[imt]
    except KeyError:
        sys.exit(
            '%s not found. The available IMTs are %s' % (imt, list(imtls)))
    imt2idx = {imt: i for i, imt in enumerate(imtls)}
    head = ['site_id'] if files else ['site_id', 'calc_id']
    if what == 'hcurves':
        array_imt = arrays[:, :, imtls(imt)]
        header = head + ['%.5f' % lvl for lvl in levels]
    else:  # hmaps
        array_imt = arrays[:, :, imt2idx[imt]]
        header = head + [str(poe) for poe in poes]
    rows = collections.defaultdict(list)
    diff_idxs = get_diff_idxs(array_imt, rtol, atol)
    if len(diff_idxs) == 0:
        print('There are no differences within the tolerance of %d%%' %
              (rtol * 100))
        return
    arr = array_imt.transpose(1, 0, 2)  # shape (N, C, L)
    for sid, array in sorted(zip(sids[diff_idxs], arr[diff_idxs])):
        for calc_id, cols in zip(calc_ids, array):
            if files:
                rows[calc_id].append([sid] + list(cols))
            else:
                rows['all'].append([sid, calc_id] + list(cols))
    if files:
        fdict = {calc_id: open('%s.txt' % calc_id, 'w')
                 for calc_id in calc_ids}
        for calc_id, f in fdict.items():
            f.write(views.rst_table(rows[calc_id], header))
            print('Generated %s' % f.name)
    else:
        print(views.rst_table(rows['all'], header))


compare.arg('what', 'hmaps or hcurves', choices={'hmaps', 'hcurves'})
compare.arg('imt', 'intensity measure type to compare')
compare.arg('calc_ids', 'calculation IDs', type=int, nargs='+')
compare.flg('files', 'write the results in multiple files')
compare.opt('samplesites', 'number of sites to sample', type=int)
compare.opt('rtol', 'relative tolerance', type=float)
compare.opt('atol', 'absolute tolerance', type=float)
