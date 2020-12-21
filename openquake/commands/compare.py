# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2020 GEM Foundation
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
from openquake.commonlib import util
from openquake.calculators.extract import Extractor
from openquake.calculators import views


def getdata(what, calc_ids, sitecol, sids):
    extractors = [Extractor(calc_id) for calc_id in calc_ids]
    extractor = extractors[0]
    oq = extractor.oqparam
    imtls = oq.imtls
    poes = oq.poes
    arrays = [extractor.get(what + '?kind=mean').mean[sids]]
    extractor.close()
    for extractor in extractors[1:]:
        oq = extractor.oqparam
        numpy.testing.assert_array_equal(
            extractor.get('sitecol')[['lon', 'lat']], sitecol[['lon', 'lat']])
        if what == 'hcurves':
            numpy.testing.assert_array_equal(oq.imtls.array, imtls.array)
        elif what == 'hmaps':
            numpy.testing.assert_array_equal(oq.poes, poes)
        arrays.append(extractor.get(what + '?kind=mean').mean[sids])
        extractor.close()
    return imtls, poes, numpy.array(arrays)  # shape (C, N, L)


def get_diff_idxs(array, rtol, atol, threshold):
    """
    Given an array with (C, N, L) values, being the first the reference value,
    compute the relative differences and discard the one below the tolerance.
    :returns: indices where there are sensible differences.
    """
    C, N, L = array.shape
    diff_idxs = set()  # indices of the sites with differences
    for n in range(N):
        if (array[:, n, 0] < threshold).all():
            continue
        for c in range(1, C):
            if not numpy.allclose(array[c, n], array[0, n], rtol, atol):
                diff_idxs.add(n)
    return numpy.fromiter(diff_idxs, int)


def _print_diff(a1, a2, idx1, idx2, col):
    if col.endswith('_'):
        for i, (v1, v2) in enumerate(zip(a1, a2)):
            idx = numpy.where(numpy.abs(v1-v2) > 1e-5)
            if len(idx[0]):
                print(col, idx1[i], v1[idx])
                print(col, idx2[i], v2[idx])
                break
    else:
        i, = numpy.where(numpy.abs(a1-a2) > 1e-5)
        if len(i):
            print(col, idx1[i], a1[i])
            print(col, idx2[i], a2[i])


def compare_rups(calc_1, calc_2):
    """
    Compare the ruptures of two calculations as pandas DataFrames
    """
    with util.read(calc_1) as ds1, util.read(calc_2) as ds2:
        df1 = ds1.read_df('rup').sort_values(['src_id', 'mag'])
        df2 = ds2.read_df('rup').sort_values(['src_id', 'mag'])
    cols = [col for col in df1.columns if col not in
            {'probs_occur_', 'clon_', 'clat_'}]
    for col in cols:
        a1 = df1[col].to_numpy()
        a2 = df2[col].to_numpy()
        assert len(a1) == len(a2), (len(a1), len(a2))
        _print_diff(a1, a2, df1.index, df2.index, col)


@sap.script
def compare(what, imt, calc_ids, files, samplesites='', rtol=0, atol=1E-3,
            threshold=1E-2):
    """
    Compare the hazard curves or maps of two or more calculations.
    Also used to compare the times with `oq compare cumtime of -1 -2`.
    """
    if what == 'cumtime':
        data = []
        for calc_id in calc_ids:
            time = Extractor(calc_id).get('performance_data')['time_sec'].sum()
            data.append((calc_id, time))
        print(views.rst_table(data, ['calc_id', 'time']))
        return
    if what == 'rups':
        return compare_rups(int(imt), calc_ids[0])
    sitecol = Extractor(calc_ids[0]).get('sitecol')
    sids = sitecol['sids']
    if samplesites:
        try:
            numsamples = int(samplesites)  # number
        except ValueError:  # filename
            sids = [int(sid) for sid in open(samplesites).read().split()]
        else:
            if len(sitecol) > numsamples:
                numpy.random.seed(numsamples)
                sids = numpy.random.choice(
                    len(sitecol), numsamples, replace=False)
    sids.sort()
    imtls, poes, arrays = getdata(what, calc_ids, sitecol, sids)
    imti = {imt: i for i, imt in enumerate(imtls)}
    try:
        levels = imtls[imt]
    except KeyError:
        sys.exit(
            '%s not found. The available IMTs are %s' % (imt, list(imtls)))
    imt2idx = {imt: i for i, imt in enumerate(imtls)}
    head = ['site_id'] if files else ['site_id', 'calc_id']
    if what == 'hcurves':
        array_imt = arrays[:, :, imti[imt], :]  # shape (C, N, L1)
        header = head + ['%.5f' % lvl for lvl in levels]
    else:  # hmaps
        array_imt = arrays[:, :, imt2idx[imt]]
        header = head + [str(poe) for poe in poes]
    rows = collections.defaultdict(list)
    diff_idxs = get_diff_idxs(array_imt, rtol, atol, threshold)
    if len(diff_idxs) == 0:
        print('There are no differences within the tolerances '
              'atol=%s, rtol=%d%%, threshold=%s, sids=%s' %
              (atol, rtol * 100, threshold, sids))
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
        if len(calc_ids) == 2 and what == 'hmaps':
            ms = numpy.mean((array_imt[0] - array_imt[1])**2, axis=0)  # P
            rows = [(str(poe), m) for poe, m in zip(poes, numpy.sqrt(ms))]
            print(views.rst_table(rows, ['poe', 'rms-diff']))


compare.arg('what', '"hmaps", "hcurves" or "cumtime of"',
            choices={'rups', 'hmaps', 'hcurves', 'cumtime'})
compare.arg('imt', 'intensity measure type to compare')
compare.arg('calc_ids', 'calculation IDs', type=int, nargs='+')
compare.flg('files', 'write the results in multiple files')
compare.opt('samplesites', 'sites to sample (or fname with site IDs)')
compare.opt('rtol', 'relative tolerance', type=float)
compare.opt('atol', 'absolute tolerance', type=float)
compare.opt('threshold', 'ignore the hazard curves below it', type=float)
