# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2021 GEM Foundation
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
from openquake.commonlib import datastore
from openquake.calculators.extract import Extractor
from openquake.calculators import views


def get_diff_idxs(array, rtol, atol):
    """
    Given an array with (C, N, L) values, being the first the reference value,
    compute the relative differences and discard the one below the tolerance.
    :returns: indices where there are sensible differences.
    """
    C, N, L = array.shape
    diff_idxs = set()  # indices of the sites with differences
    for n in range(N):
        for c in range(1, C):
            if not numpy.allclose(array[c, n], array[0, n], rtol, atol):
                diff_idxs.add(n)
    return numpy.fromiter(diff_idxs, int)


def _print_diff(a1, a2, idx1, idx2, col):
    if col.endswith('_'):
        for i, (v1, v2) in enumerate(zip(a1, a2)):
            idx = numpy.where(numpy.abs(v1-v2) > 1e-5)
            if len(idx[0]):
                print(col, v1[idx], v2[idx])
                break
    else:
        i, = numpy.where(numpy.abs(a1-a2) > 1e-5)
        if len(i):
            print(col, idx1[i], a1[i])
            print(col, idx2[i], a2[i])


def get_mean(extractor, what, sids, imtls, p):
    mean = extractor.get(what).mean[sids, :, p]  # shape (N, M)
    mu = numpy.array([mean[:, m] for m, imt in enumerate(imtls)
                      if imt.startswith(('PGA', 'SA'))]).T  # (N, M')
    return mu.reshape(len(sids), -1)  # shape N * M'


class Comparator(object):
    def __init__(self, calc_ids):
        self.extractors = [Extractor(calc_id) for calc_id in calc_ids]
        self.sitecol = self.extractors[0].get('sitecol')
        self.oq = self.extractors[0].oqparam

    def cumtime(self):
        data = []
        for ex in self.extractors:
            time = ex.get('performance_data')['time_sec'].sum()
            data.append((ex.calc_id, time))
        print(views.text_table(data, ['calc_id', 'time']))

    def getsids(self, samplesites):
        sids = self.sitecol['sids']
        if samplesites:
            try:
                numsamples = int(samplesites)  # number
            except ValueError:  # filename
                sids = [int(sid) for sid in open(samplesites).read().split()]
            else:
                if len(self.sitecol) > numsamples:
                    numpy.random.seed(numsamples)
                    sids = numpy.random.choice(
                        len(self.sitecol), numsamples, replace=False)
        return numpy.sort(sids)

    def getdata(self, what, imt, sids):
        oq = self.oq
        extractor = self.extractors[0]
        imtls = oq.imtls
        poes = oq.poes
        if imt not in imtls:
            sys.exit('%s not found. The available IMTs are %s' %
                     (imt, list(imtls)))
        imti = {imt: i for i, imt in enumerate(imtls)}
        m = imti[imt]
        what += '?kind=mean&imt=' + imt
        arrays = [extractor.get(what).mean[sids, m, :]]
        extractor.close()
        for extractor in self.extractors[1:]:
            oq = extractor.oqparam
            if what.startswith('hcurves'):  # array NML
                numpy.testing.assert_array_equal(oq.imtls[imt], imtls[imt])
            elif what.startswith('hmaps'):  # array NMP
                numpy.testing.assert_array_equal(oq.poes, poes)
            arrays.append(extractor.get(what).mean[sids, m, :])
            extractor.close()
        return numpy.array(arrays)  # shape (C, N, L)

    def getuhs(self, what, p, sids):
        # uhs for the first poe
        oq0 = self.oq
        extractor = self.extractors[0]
        what = 'hmaps?kind=mean'  # shape (N, M, P)
        arrays = [get_mean(extractor, what, sids, oq0.imtls, p)]
        extractor.close()
        for extractor in self.extractors[1:]:
            oq = extractor.oqparam
            numpy.testing.assert_array_equal(oq.imtls.array, oq0.imtls.array)
            numpy.testing.assert_array_equal(oq.poes, oq0.poes)
            arrays.append(get_mean(extractor, what, sids, oq0.imtls, p))
            extractor.close()
        return numpy.array(arrays)  # shape (C, N, M*P)

    def getgmf(self, what, imt, sids):
        extractor = self.extractors[0]
        imtls = self.oq.imtls
        if imt not in imtls:
            sys.exit('%s not found. The available IMTs are %s' %
                     (imt, list(imtls)))
        what += '?imt=' + imt
        aw = extractor.get(what)
        arrays = numpy.zeros((len(self.extractors), len(sids), 1))
        arrays[0, :, 0] = getattr(aw, imt)[sids]
        extractor.close()
        for e, extractor in enumerate(self.extractors[1:], 1):
            arrays[e, :, 0] = getattr(extractor.get(what), imt)[sids]
            extractor.close()
        return arrays  # shape (C, N, 1)

    def compare(self, what, imt, files, samplesites, atol, rtol):
        sids = self.getsids(samplesites)
        if what == 'uhs':
            arrays = self.getuhs(what, imt, sids)
        elif what.startswith('avg_gmf'):
            arrays = self.getgmf(what, imt, sids)
        else:
            arrays = self.getdata(what, imt, sids)
        header = ['site_id'] if files else ['site_id', 'calc_id']
        if what == 'hcurves':
            header += ['%.5f' % lvl for lvl in self.oq.imtls[imt]]
        elif what == 'hmaps':
            header += [str(poe) for poe in self.oq.poes]
        elif what == 'uhs':
            header += self.oq.imt_periods()
        else:  # avg_gmf
            header += ['gmf']
        rows = collections.defaultdict(list)
        diff_idxs = get_diff_idxs(arrays, rtol, atol)
        if len(diff_idxs) == 0:
            print('There are no differences within the tolerances '
                  'atol=%s, rtol=%d%%, sids=%s' % (atol, rtol * 100, sids))
            return []
        arr = arrays.transpose(1, 0, 2)  # shape (N, C, L)
        for sid, array in sorted(zip(sids[diff_idxs], arr[diff_idxs])):
            # each array has shape (C, L)
            for ex, cols in zip(self.extractors, array):
                # cols has shape L
                if files:
                    rows[ex.calc_id].append([sid] + list(cols))
                else:
                    rows['all'].append([sid, ex.calc_id] + list(cols))
        if files:
            fdict = {ex.calc_id: open('%s.txt' % ex.calc_id, 'w')
                     for ex in self.extractors}
            for calc_id, f in fdict.items():
                f.write(views.text_table(rows[calc_id], header))
                print('Generated %s' % f.name)
        else:
            print(views.text_table(rows['all'], header))
        return arrays


# works only locally for the moment
def compare_rups(calc_1: int, calc_2: int):
    """
    Compare the ruptures of two calculations as pandas DataFrames
    """
    with datastore.read(calc_1) as ds1, datastore.read(calc_2) as ds2:
        df1 = ds1.read_df('rup').sort_values(['src_id', 'mag'])
        df2 = ds2.read_df('rup').sort_values(['src_id', 'mag'])
    cols = [col for col in df1.columns if col not in
            {'probs_occur_', 'clon_', 'clat_'}]
    for col in cols:
        a1 = df1[col].to_numpy()
        a2 = df2[col].to_numpy()
        assert len(a1) == len(a2), (len(a1), len(a2))
        _print_diff(a1, a2, df1.index, df2.index, col)


def compare_cumtime(calc1: int, calc2: int):
    """
    Compare the cumulative times between too calculations
    """
    return Comparator([calc1, calc2]).cumtime()


def compare_uhs(calc_ids: int, files=False, *, poe_id: int = 0,
                samplesites='', rtol: float = 0, atol: float = 1E-3):
    """
    Compare the uniform hazard spectra of two or more calculations.
    """
    c = Comparator(calc_ids)
    arrays = c.compare('uhs', poe_id, files, samplesites, atol, rtol)
    if len(arrays) and len(calc_ids) == 2:
        # each array has shape (N, M)
        ms = numpy.mean((arrays[0] - arrays[1])**2)
        maxdiff = numpy.abs(arrays[0] - arrays[1]).max()
        row = ('%.5f' % c.oq.poes[poe_id], numpy.sqrt(ms), maxdiff)
        print(views.text_table([row], ['poe', 'rms-diff', 'max-diff']))


def compare_hmaps(imt, calc_ids: int, files=False, *,
                  samplesites='', rtol: float = 0, atol: float = 1E-3):
    """
    Compare the hazard maps of two or more calculations.
    """
    c = Comparator(calc_ids)
    arrays = c.compare('hmaps', imt, files, samplesites, atol, rtol)
    if len(arrays) and len(calc_ids) == 2:
        ms = numpy.mean((arrays[0] - arrays[1])**2, axis=0)  # P
        maxdiff = numpy.abs(arrays[0] - arrays[1]).max(axis=0)  # P
        rows = [(str(poe), rms, md) for poe, rms, md in zip(
            c.oq.poes, numpy.sqrt(ms), maxdiff)]
        print(views.text_table(rows, ['poe', 'rms-diff', 'max-diff']))


def compare_hcurves(imt, calc_ids: int, files=False, *,
                    samplesites='', rtol: float = 0, atol: float = 1E-3):
    """
    Compare the hazard curves of two or more calculations.
    """
    c = Comparator(calc_ids)
    c.compare('hcurves', imt, files, samplesites, atol, rtol)


def compare_avg_gmf(imt, calc_ids: int, files=False, *,
                    samplesites='', rtol: float = 0, atol: float = 1E-3):
    """
    Compare the average GMF of two or more calculations.
    """
    c = Comparator(calc_ids)
    arrays = c.compare('avg_gmf', imt, files, samplesites, atol, rtol)
    if len(calc_ids) == 2:  # print rms-diff
        gmf1, gmf2 = arrays
        sigma = numpy.sqrt(numpy.average((gmf1 - gmf2)**2))
        print('rms-diff =', sigma)


main = dict(rups=compare_rups,
            cumtime=compare_cumtime,
            uhs=compare_uhs,
            hmaps=compare_hmaps,
            hcurves=compare_hcurves,
            avg_gmf=compare_avg_gmf)

for f in (compare_uhs, compare_hmaps, compare_hcurves, compare_avg_gmf):
    if f is compare_uhs:
        f.poe_id = 'index of the PoE (or return period)'
    else:
        f.imt = 'intensity measure type to compare'
    f.calc_ids = dict(help='calculation IDs', nargs='+')
    f.files = 'write the results in multiple files'
    f.samplesites = 'sites to sample (or fname with site IDs)'
    f.rtol = 'relative tolerance'
    f.atol = 'absolute tolerance'
