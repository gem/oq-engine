# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2025 GEM Foundation
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

import os
import sys
import collections
import numpy
import pandas
from openquake.commonlib import datastore
from openquake.calculators.extract import Extractor
from openquake.calculators import views

aac = numpy.testing.assert_allclose
F64 = numpy.float64


def get_diff_idxs(array, rtol, atol):
    """
    Given an array with (C, N, L) values, being the first the reference value,
    compute the relative differences and discard the one below the tolerance.
    :returns: indices where there are sensible differences.
    """
    C, N, _L = array.shape
    diff_idxs = set()  # indices of the sites with differences
    for n in range(N):
        for c in range(1, C):
            if not numpy.allclose(array[c, n], array[0, n], rtol, atol):
                diff_idxs.add(n)
    return numpy.fromiter(diff_idxs, int)


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
        print(views.text_table(data, ['calc_id', 'time'], ext='org'))

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

    def getdata(self, what, imt, sids, rtol, atol):
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
                aac(oq.imtls[imt], imtls[imt], rtol, atol)
            elif what.startswith('hmaps'):  # array NMP
                aac(oq.poes, poes, rtol, atol)
            arrays.append(extractor.get(what).mean[sids, m, :])
            extractor.close()
        return numpy.array(arrays)  # shape (C, N, L)

    def getuhs(self, what, p, sids, rtol, atol):
        # uhs for the last poe
        oq0 = self.oq
        extractor = self.extractors[0]
        what = 'hmaps?kind=mean'  # shape (N, M, P)
        arrays = [get_mean(extractor, what, sids, oq0.imtls, p)]
        high_sites = [extractor.get('high_sites').array]
        extractor.close()
        for extractor in self.extractors[1:]:
            oq = extractor.oqparam
            aac(oq.imtls.array, oq0.imtls.array, rtol, atol)
            aac(oq.poes, oq0.poes, rtol, atol)
            high_sites.append(extractor.get('high_sites').array)
            arrays.append(get_mean(extractor, what, sids, oq0.imtls, p))
            extractor.close()
        hsites = numpy.logical_and(*high_sites)
        sids, = numpy.where(hsites)
        return numpy.array([a[hsites] for a in arrays]), sids  # shape (C, N, M*P)

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

    def compare(self, what, imt, files, samplesites, rtol, atol):
        sids = self.getsids(samplesites)
        if what == 'uhs':  # imt is -1, the last poe
            arrays, sids = self.getuhs(what, imt, sids, rtol, atol)
        elif what.startswith('avg_gmf'):
            arrays = self.getgmf(what, imt, sids)
        else:
            arrays = self.getdata(what, imt, sids, rtol, atol)
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
            return (), ()
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
                f.write(views.text_table(rows[calc_id], header, ext='org'))
                print('Generated %s' % f.name)
        else:
            print(views.text_table(rows['all'], header, ext='org'))
        if what == 'uhs':
            return arrays, sids
        return arrays


def compare_rates(calc_1: int, calc_2: int):
    """
    Compare the ruptures affecting the given site ID as pandas DataFrames
    """
    with datastore.read(calc_1) as ds1, datastore.read(calc_2) as ds2:
        df1 = ds1.read_df('_rates', ['gid', 'sid', 'lid'])
        df2 = ds2.read_df('_rates', ['gid', 'sid', 'lid'])
    delta = numpy.abs(df1 - df2).to_numpy().max()
    print('Maximum difference in the rates =%s' % delta)


# works only locally for the moment
def compare_rups(calc_1: int, calc_2: int, site_id: int = 0):
    """
    Compare the ruptures affecting the given site ID as pandas DataFrames
    """
    sort = ['src_id', 'rup_id']
    with datastore.read(calc_1) as ds1, datastore.read(calc_2) as ds2:
        df1 = ds1.read_df('rup', sel={'sids': site_id}).sort_values(sort)
        df2 = ds2.read_df('rup', sel={'sids': site_id}).sort_values(sort)
    del df1['probs_occur']
    del df2['probs_occur']
    lens = len(df1), len(df2)
    if lens[0] != lens[1]:
        print('%d != %d ruptures' % lens)
        return
    df2.index = df1.index
    print(df1.compare(df2))


def compare_cumtime(calc1: int, calc2: int):
    """
    Compare the cumulative times between too calculations
    """
    return Comparator([calc1, calc2]).cumtime()


def compare_uhs(calc_ids: int, files=False, *, poe_id: int = -1,
                samplesites='', rtol: float = 0, atol: float = 1E-3):
    """
    Compare the uniform hazard spectra of two or more calculations.
    """
    c = Comparator(calc_ids)
    arrays, sids = c.compare('uhs', poe_id, files, samplesites, rtol, atol)
    if len(arrays) and len(calc_ids) == 2:
        # each array has shape (N, M)
        rms = numpy.sqrt(numpy.mean((arrays[0] - arrays[1])**2))
        delta = numpy.abs(arrays[0] - arrays[1]).max(axis=1)
        amax = delta.argmax()
        row = ('%.5f' % c.oq.poes[poe_id], rms, delta[amax], sids[amax])
        print(views.text_table([row], ['poe', 'rms-diff', 'max-diff', 'site'],
                               ext='org'))


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
        print(views.text_table(rows, ['poe', 'rms-diff', 'max-diff'],
                               ext='org'))


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
    arrays = c.compare('avg_gmf', imt, files, samplesites, rtol, atol)
    if len(calc_ids) == 2:  # print rms-diff
        gmf1, gmf2 = arrays
        if len(gmf1):
            sigma = numpy.sqrt(numpy.average((gmf1 - gmf2)**2))
            print('rms-diff =', sigma)


def compare_med_gmv(imt, calc_ids: int, *,
                    rtol: float = 0, atol: float = 1E-3):
    """
    Compare the median GMVs of two calculations.
    """
    c = Comparator(calc_ids)
    try:
        [m] = set(list(ex.oqparam.imtls).index(imt) for ex in c.extractors)
    except ValueError:
        sys.exit('The imt %s is not present in all calculations' % imt)
    ex1, ex2 = c.extractors
    srcs1 = sorted(ex1.get('med_gmv'))
    srcs2 = sorted(ex2.get('med_gmv'))
    if srcs1 != srcs2:
        raise ValueError(set(srcs1).symmetric_difference(srcs2))
    for src in srcs1:
        # arrays of shape (G, M, N) => (G, N)
        aw1 = ex1.get(f'med_gmv/{src}')
        aw2 = ex2.get(f'med_gmv/{src}')
        assert list(aw1.gsims) == list(aw2.gsims), (aw1.gsims, aw2.gsims)
        arr1 = aw1[:, m]
        arr2 = aw2[:, m]
        aac(arr1.shape, arr2.shape, rtol, atol)
        if numpy.allclose(arr1, arr2, rtol, atol):
            print(f'{src}: no differences within the tolerances '
                  f'{atol=}, rtol={rtol*100}%')
        else:
            for g in range(len(arr1)):
                a1, a2 = arr1[g], arr2[g]
                if not numpy.allclose(a1, a2, rtol, atol):
                    n = numpy.abs(a1 - a2).argmax()
                    print('%s%s: %s vs %s' % (src, aw1.gsims[g], a1[n], a2[n]))


# works only locally for the moment
def compare_risk_by_event(event: int, calc_ids: int, *,
                          rtol: float = 0, atol: float = 1E-3):
    """
    Compare risk_by_event for a given event across two calculations.
    Raise an error if the GMFs are not compatible.
    """
    ds0 = datastore.read(calc_ids[0])
    ds1 = datastore.read(calc_ids[1])
    df0 = ds0.read_df('gmf_data', 'sid', sel={'eid': event})
    df1 = ds1.read_df('gmf_data', 'sid', sel={'eid': event})
    df = df0.compare(df1)
    if len(df):
        print('Not comparable GMFs: %s', df)
        return
    df0 = ds0.read_df('risk_by_event', 'agg_id', sel={'event_id': event})
    df1 = ds1.read_df('risk_by_event', 'agg_id', sel={'event_id': event})
    print(df0)
    print(df1)


def compare_sources(calc_ids: int):
    """
    Compare source_info DataFrames
    """
    ds0 = datastore.read(calc_ids[0])
    ds1 = datastore.read(calc_ids[1])
    header = ['source_id', 'grp_id', 'code', 'num_ruptures']
    df0 = ds0.read_df('source_info')[header]
    df1 = ds1.read_df('source_info')[header]
    df = df0.compare(df1)
    print(df)


def compare_events(calc_ids: int):
    """
    Compare events DataFrames
    """
    ds0 = datastore.read(calc_ids[0])
    ds1 = datastore.read(calc_ids[1])
    df0 = ds0.read_df('events', 'rup_id')
    df1 = ds1.read_df('events', 'rup_id')
    df = df0.compare(df1)
    print(df)


def delta(a, b):
    """
    :returns: the relative differences between a and b; zeros return zeros
    """
    c = a + b
    ok = c != 0.
    res = numpy.zeros_like(a)
    res[ok] = numpy.abs(a[ok] - b[ok]) / c[ok]
    return res


def compare_column_values(array0, array1, what, atol=0, rtol=1E-5):
    try:
        array0 = F64(array0)
        array1 = F64(array1)
    except ValueError:
        diff_idxs = numpy.where(array0 != array1)[0]
    else:
        diff = numpy.abs(array0 - array1)
        diff_idxs = numpy.where(diff > atol + (array0+array1)/2 * rtol)[0]
    if len(diff_idxs) == 0:
        print(f'The column {what} is okay')
        return True
    print(f"There are {len(diff_idxs)} different elements "
          f"in the '{what}' column:")
    print(array0[diff_idxs], array1[diff_idxs], diff_idxs)


def check_column_names(array0, array1, what, calc_id0, calc_id1):
    cols0 = array0.dtype.names
    cols1 = array1.dtype.names
    if len(cols0) != len(cols1):
        print(f'The {what} arrays have different columns:')
        print(f'Calc {calc_id0}:\n{cols0}')
        print(f'Calc {calc_id1}:\n{cols1}')
    elif numpy.array_equal(cols0, cols1):
        print(f'The {what} arrays have the same columns')
    elif numpy.array_equal(numpy.sort(cols0), numpy.sort(cols1)):
        print(f'The {what} arrays have the same columns, but ordered'
              ' differently')
    else:
        print(f'The {what} arrays have differend columns:')
        print(f'Calc {calc_id0}:\n{cols0}')
        print(f'Calc {calc_id1}:\n{cols1}')


def compare_assetcol(calc_ids: int):
    """
    Compare assetcol DataFrames
    """
    ds0 = datastore.read(calc_ids[0])
    ds1 = datastore.read(calc_ids[1])
    array0 = ds0['assetcol'].array
    array1 = ds1['assetcol'].array
    oq0 = ds0['oqparam']
    oq1 = ds1['oqparam']
    if oq0.impact:
        array0['id'] = [id[3:] for id in array0['id']]
    if oq1.impact:
        array1['id'] = [id[3:] for id in array1['id']]
    check_column_names(array0, array1, 'assetcol', *calc_ids)
    fields = set(array0.dtype.names) & set(array1.dtype.names) - {
        'site_id', 'id', 'ordinal', 'taxonomy'}
    arr0, arr1 = check_intersect(
        array0, array1, 'id', sorted(fields), calc_ids)
    taxo0 = ds0['assetcol/tagcol/taxonomy'][:][arr0['taxonomy']]
    taxo1 = ds1['assetcol/tagcol/taxonomy'][:][arr1['taxonomy']]
    compare_column_values(taxo0, taxo1, 'taxonomy')


def check_intersect(array0, array1, kfield, vfields, calc_ids):
    """
    Compare two structured arrays on the given field
    """
    array0.sort(order=kfield)
    array1.sort(order=kfield)
    val0 = array0[kfield]
    val1 = array1[kfield]
    common = numpy.intersect1d(val0, val1, assume_unique=True)
    print(f'Comparing {kfield=}, {len(val0)=}, {len(val1)=}, {len(common)=}')
    if len(val0) < len(val1):
        print('A missing asset is %s' % (set(val1)-set(val0)).pop())
    elif len(val1) < len(val0):
        print('A missing asset is %s' % (set(val0)-set(val1)).pop())
    arr0 = array0[numpy.isin(val0, common)]
    arr1 = array1[numpy.isin(val1, common)]
    for col in vfields:
        compare_column_values(arr0[col], arr1[col], col)
    return arr0, arr1


def compare_sitecol(calc_ids: int):
    """
    Compare the site collections of two calculations, looking for similarities
    """
    ds0 = datastore.read(calc_ids[0])
    ds1 = datastore.read(calc_ids[1])
    array0 = ds0['sitecol'].array
    array1 = ds1['sitecol'].array
    check_column_names(array0, array1, 'sitecol', *calc_ids)
    fields = set(array0.dtype.names) & set(array1.dtype.names) - {'sids'}
    if 'custom_site_id' in fields:
        check_intersect(
            array0, array1, 'custom_site_id',
            sorted(fields-{'custom_site_id'}), calc_ids)
    else:
        check_intersect(array0, array1, 'sids', sorted(fields), calc_ids)


def compare_oqparam(calc_ids: int):
    """
    Compare the dictionaries of parameters associated to the calculations
    """
    ds0 = datastore.read(calc_ids[0])
    ds1 = datastore.read(calc_ids[1])
    dic0 = vars(ds0['oqparam'])
    dic1 = vars(ds1['oqparam'])
    common = set(dic0) & set(dic1) - {'hdf5path'}
    for key in sorted(common):
        if dic0[key] != dic1[key]:
            print('%s: %s != %s' % (key, dic0[key], dic1[key]))


def strip(values):
    if isinstance(values[0], str):
        return numpy.array([s.strip() for s in values])
    return values


def read_org_df(fname):
    df = pandas.read_csv(fname, delimiter='|',
                          skiprows=lambda r: r == 1)
    df = df[df.columns[1:-1]]
    return df.rename(columns=dict(zip(df.columns, strip(df.columns))))


def compare_asce(dir1: str, dir2: str, atol=1E-3, rtol=1E-3):
    """
    compare_asce('asce', 'expected') exits with 0
    if all file are equal within the tolerance, otherwise with 1.
    """
    for fname in os.listdir(dir2):
        if fname.endswith('.org'):
            print(f"Comparing {fname}")
            df1 = read_org_df(os.path.join(dir1, fname))
            df2 = read_org_df(os.path.join(dir2, fname))
            equal = []
            for col in df1.columns:
                ok = compare_column_values(strip(df1[col].to_numpy()),
                                           strip(df2[col].to_numpy()),
                                           col, atol, rtol)
                equal.append(ok)
            if not all(equal):
                sys.exit(1)


main = dict(rups=compare_rups,
            cumtime=compare_cumtime,
            uhs=compare_uhs,
            hmaps=compare_hmaps,
            hcurves=compare_hcurves,
            rates=compare_rates,
            avg_gmf=compare_avg_gmf,
            med_gmv=compare_med_gmv,
            risk_by_event=compare_risk_by_event,
            sources=compare_sources,
            events=compare_events,
            assetcol=compare_assetcol,
            sitecol=compare_sitecol,
            oqparam=compare_oqparam,
            asce=compare_asce)

for f in (compare_uhs, compare_hmaps, compare_hcurves, compare_avg_gmf,
          compare_med_gmv, compare_risk_by_event, compare_sources,
          compare_events, compare_assetcol, compare_sitecol, compare_oqparam):
    if f is compare_uhs:
        f.poe_id = 'index of the PoE (or return period)'
    elif f is compare_risk_by_event:
        f.event = 'event index'
    else:
        f.imt = 'intensity measure type to compare'
    f.calc_ids = dict(help='calculation IDs', nargs='+')
    f.files = 'write the results in multiple files'
    f.samplesites = 'sites to sample (or fname with site IDs)'
    f.rtol = 'relative tolerance'
    f.atol = 'absolute tolerance'
