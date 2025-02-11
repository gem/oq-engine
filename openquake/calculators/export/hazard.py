# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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

import re
import os
import sys
import json
import itertools
import collections
import numpy
import pandas

from openquake.baselib.general import DictArray, AccumDict
from openquake.baselib import hdf5, writers
from openquake.baselib.python3compat import decode
from openquake.calculators.views import view, text_table
from openquake.calculators.extract import extract, get_sites, get_info
from openquake.calculators.export import export
from openquake.commonlib import calc, util

F32 = numpy.float32
F64 = numpy.float64
U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32

# with compression you can save 60% of space by losing only 10% of saving time
savez = numpy.savez_compressed


def add_quotes(values):
    # used to source names in CSV files
    return ['"%s"' % val for val in values]


@export.add(('ruptures', 'csv'))
def export_ruptures_csv(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    oq = dstore['oqparam']
    if 'scenario' in oq.calculation_mode:
        return []
    dest = dstore.export_path('ruptures.csv')
    arr = extract(dstore, 'rupture_info')
    if export.sanity_check:
        bad = view('bad_ruptures', dstore)
        if len(bad):  # nonempty
            print(text_table(bad), file=sys.stderr)
    comment = dstore.metadata
    comment.update(investigation_time=oq.investigation_time,
                   ses_per_logic_tree_path=oq.ses_per_logic_tree_path)
    arr.array.sort(order='rup_id')
    writers.write_csv(dest, arr, comment=comment)
    return [dest]


# ####################### export hazard curves ############################ #

HazardCurve = collections.namedtuple('HazardCurve', 'location poes')


def export_hmaps_csv(key, dest, sitemesh, array, comment):
    """
    Export the hazard maps of the given realization into CSV.

    :param key: output_type and export_type
    :param dest: name of the exported file
    :param sitemesh: site collection
    :param array: a composite array of dtype hmap_dt
    :param comment: comment to use as header of the exported CSV file
    """
    curves = util.compose_arrays(sitemesh, array)
    writers.write_csv(dest, curves, comment=comment)
    return [dest]


def add_imt(fname, imt):
    """
    >>> orig_path = '/path/to/hcurve_23.csv'
    >>> new_path = add_imt(orig_path, 'SA(0.1)')
    >>> os.path.dirname(new_path) == os.path.dirname(orig_path)
    True
    >>> os.path.basename(new_path)
    'hcurve-SA(0.1)_23.csv'
    """
    name = os.path.basename(fname)
    newname = re.sub(r'(_\d+\.)', '-%s\\1' % imt, name)
    return os.path.join(os.path.dirname(fname), newname)


def export_hcurves_by_imt_csv(
        key, kind, fname, sitecol, array, imt, imls, comment):
    """
    Export the curves of the given realization into CSV.

    :param key: output_type and export_type
    :param kind: a string with the kind of output (realization or statistics)
    :param fname: name of the exported file
    :param sitecol: site collection
    :param array: an array of shape (N, 1, L1) and dtype numpy.float32
    :param imt: intensity measure type
    :param imls: intensity measure levels
    :param comment: comment dictionary
    """
    nsites = len(sitecol)
    dest = add_imt(fname, imt)
    lst = [('lon', F32), ('lat', F32), ('depth', F32)]
    for iml in imls:
        lst.append(('poe-%.7f' % iml, F32))
    custom = 'custom_site_id' in sitecol.array.dtype.names
    if custom:
        lst.insert(0, ('custom_site_id', 'S8'))
    hcurves = numpy.zeros(nsites, lst)
    if custom:
        for sid, csi, lon, lat, dep in zip(
                range(nsites), sitecol.custom_site_id,
                sitecol.lons, sitecol.lats, sitecol.depths):
            hcurves[sid] = (csi, lon, lat, dep) + tuple(array[sid, 0, :])
    else:
        hcurves = numpy.zeros(nsites, lst)
        for sid, lon, lat, dep in zip(
                range(nsites), sitecol.lons, sitecol.lats, sitecol.depths):
            hcurves[sid] = (lon, lat, dep) + tuple(array[sid, 0, :])
    comment.update(imt=imt)
    
    
    return writers.write_csv(dest, hcurves, comment=comment,
                             header=[name for (name, dt) in lst])


def hazard_curve_name(dstore, ekey, kind):
    """
    :param calc_id: the calculation ID
    :param ekey: the export key
    :param kind: the kind of key
    """
    key, fmt = ekey
    prefix = {'hcurves': 'hazard_curve', 'hmaps': 'hazard_map',
              'uhs': 'hazard_uhs'}[key]
    if kind.startswith('quantile-'):  # strip the 7 characters 'hazard_'
        fname = dstore.build_fname('quantile_' + prefix[7:], kind[9:], fmt)
    else:
        fname = dstore.build_fname(prefix, kind, fmt)
    return fname


def get_kkf(ekey):
    """
    :param ekey: export key, for instance ('uhs/rlz-1', 'xml')
    :returns: key, kind and fmt from the export key, i.e. 'uhs', 'rlz-1', 'xml'
    """
    key, fmt = ekey
    if '/' in key:
        key, kind = key.split('/', 1)
    else:
        kind = ''
    return key, kind, fmt


def export_aelo_csv(key, dstore):
    """
    Export hcurves and uhs in an Excel-friendly format
    """
    # in AELO mode there is a single site and a single statistics, the mean
    assert key in ('hcurves', 'uhs')
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    lon, lat = sitecol.lons[0], sitecol.lats[0]
    fname = hazard_curve_name(dstore, (key, 'csv'), 'mean')
    comment = dstore.metadata
    comment.update(lon=lon, lat=lat, kind='mean',
                   investigation_time=oq.investigation_time)
    if key == 'hcurves':
        arr = dstore['hcurves-stats'][0, 0]  # shape (M, L1)
        M, L1 = arr.shape
        array = numpy.zeros(M*L1, [('imt', hdf5.vstr), ('iml', float),
                                   ('poe', float)])
        for m, imt in enumerate(oq.imtls):
            for li, iml in enumerate(oq.imtls[imt]):
                row = array[m*L1 + li]
                row['imt'] = imt
                row['iml'] = iml
                row['poe'] = arr[m, li]
        writers.write_csv(fname, array, comment=comment)

    elif key == 'uhs':
        arr = dstore['hmaps-stats'][0, 0]  # shape (M, P)
        periods = [imt.period for imt in oq.imt_periods()]
        poes = [('poe-%s' % poe, float) for poe in oq.poes]
        array = numpy.zeros(len(periods), [('period', float)] + poes)
        for m, period in enumerate(periods):
            row = array[m]
            row['period'] = period
            for p, poe in enumerate(oq.poes):
                row['poe-%s' % poe] = arr[m, p]
        writers.write_csv(fname, array, comment=comment)

    return [fname]


@export.add(('hcurves', 'csv'), ('hmaps', 'csv'), ('uhs', 'csv'))
def export_hcurves_csv(ekey, dstore):
    """
    Exports the hazard curves into several .csv files

    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    if os.environ.get('OQ_APPLICATION_MODE') == 'AELO':
        return export_aelo_csv(ekey[0], dstore)

    oq = dstore['oqparam']
    info = get_info(dstore)
    R = dstore['full_lt'].get_num_paths()
    sitecol = dstore['sitecol']
    sitemesh = get_sites(sitecol)
    key, kind, fmt = get_kkf(ekey)
    fnames = []
    comment = dstore.metadata
    hmap_dt = oq.hmap_dt()
    for kind in oq.get_kinds(kind, R):
        fname = hazard_curve_name(dstore, (key, fmt), kind)
        comment.update(kind=kind, investigation_time=oq.investigation_time)
        if (key in ('hmaps', 'uhs') and oq.uniform_hazard_spectra or
                oq.hazard_maps):
            hmap = extract(dstore, 'hmaps?kind=' + kind)[kind]
        if key == 'uhs' and oq.poes and oq.uniform_hazard_spectra:
            uhs_curves = calc.make_uhs(hmap, info)
            writers.write_csv(
                fname, util.compose_arrays(sitemesh, uhs_curves),
                comment=comment)
            fnames.append(fname)
        elif key == 'hmaps' and oq.poes and oq.hazard_maps:
            fnames.extend(
                export_hmaps_csv(ekey, fname, sitemesh,
                                 hmap.flatten().view(hmap_dt), comment))
        elif key == 'hcurves':
            # shape (N, R|S, M, L1)
            if ('amplification' in oq.inputs and
                    oq.amplification_method == 'convolution'):
                imtls = DictArray(
                    {imt: oq.soil_intensities for imt in oq.imtls})
            else:
                imtls = oq.imtls
            for imt, imls in imtls.items():
                hcurves = extract(
                    dstore, 'hcurves?kind=%s&imt=%s' % (kind, imt))[kind]
                fnames.append(
                    export_hcurves_by_imt_csv(
                        ekey, kind, fname, sitecol, hcurves, imt, imls,
                        comment))
    return sorted(fnames)


UHS = collections.namedtuple('UHS', 'imls location')


def get_metadata(rlzs, kind):
    """
    :param rlzs:
        realization array with field 'branch_path'
    :param str kind:
        kind of data, i.e. a key in the datastore
    :returns:
        a dictionary with smlt_path, gsimlt_path, statistics, quantile_value
    """
    metadata = {}
    if kind.startswith('rlz-'):
        smlt_path, gslt_path = rlzs[int(kind[4:])]['branch_path'].split('~')
        metadata['smlt_path'] = smlt_path
        metadata['gsimlt_path'] = gslt_path
    elif kind.startswith('quantile-'):
        metadata['statistics'] = 'quantile'
        metadata['quantile_value'] = float(kind[9:])
    elif kind == 'mean':
        metadata['statistics'] = 'mean'
    elif kind == 'max':
        metadata['statistics'] = 'max'
    elif kind == 'std':
        metadata['statistics'] = 'std'
    return metadata


@export.add(('cs-stats', 'csv'))
def export_cond_spectra(ekey, dstore):
    sitecol = dstore['sitecol']
    aw = dstore[ekey[0]]  # shape (N, P, K, M, 2)
    dframe = aw.to_dframe()
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    fnames = []
    for n in sitecol.sids:
        df = dframe[dframe.site_id == n]
        del df['site_id']
        fname = dstore.export_path('conditional-spectrum-%d.csv' % n)
        comment = dstore.metadata.copy()
        comment['site_id'] = n
        comment['lon'] = sitecol.lons[n]
        comment['lat'] = sitecol.lats[n]
        writer.save(df, fname, comment=comment)
        fnames.append(fname)
    return fnames


@export.add(('median_spectra', 'csv'))
def export_median_spectra(ekey, dstore):
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    fnames = []
    for n in sitecol.sids:
        for p, poe in enumerate(oq.poes):
            aw = extract(dstore, f'median_spectra?site_id={n}&poe_id={p}')
            Gt = len(aw.array)
            aggr = aw.array.sum(axis=0) # shape (3, P)
            df = aw.to_dframe().sort_values(['grp_id', 'period'])
            comment = dstore.metadata.copy()
            comment['site_id'] = n
            comment['lon'] = sitecol.lons[n]
            comment['lat'] = sitecol.lats[n]
            comment['poe'] = poe
            if Gt > 1:
                fname = dstore.export_path('median_spectra-%d-%d.csv' % (n, p))
                writer.save(df, fname, comment=comment)
                fnames.append(fname)
            fname = dstore.export_path('median_spectrum-%d-%d.csv' % (n, p))
            aggdf = pandas.DataFrame(dict(
                period=aw.period, spec=numpy.exp(aggr[0]),
                mea=aggr[0], sig=aggr[1], wei=aggr[2]))
            writer.save(aggdf, fname, comment=comment)
            fnames.append(fname)
    return fnames



@export.add(('median_spectrum_disagg', 'csv'))
def export_median_spectrum_disagg(ekey, dstore):
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    fnames = []
    totw = AccumDict(accum=0)
    for grp_id, dset in dstore['median_spectrum_disagg'].items():
        array = dset[:]
        dtlist = [tup[:2] for tup in array.dtype.descr]
        for m, imt in enumerate(oq.imtls):
            arr = numpy.empty(len(array), dtlist)
            for col in arr.dtype.names:
                if col.startswith(('mea', 'sig', 'wei')):
                    arr[col] = array[col][:, m]
                else:
                    arr[col] = array[col]
                if col.startswith('wei'):
                    totw[imt] += arr[col].sum()        
            comment = dstore.metadata.copy()
            comment['site_id'] = 0
            comment['lon'] = sitecol.lons[0]
            comment['lat'] = sitecol.lats[0]
            fname = dstore.export_path(f'median_spectrum_disagg-{grp_id}-{imt}.csv')
            arr.sort(order='rup_id')
            writer.save(arr, fname, comment=comment)
            fnames.append(fname)

    # sanity check on the weights
    for imt in totw:
        print('tot weight for', imt, totw[imt])
    #    assert abs(totw[imt] - 1) < .01, (imt, totw[imt])
    return fnames


# TODO: see if I can remove this
def _extract(hmap, imt, j):
    # hmap[imt] can be a tuple or a scalar if j=0
    tup = hmap[imt]
    if hasattr(tup, '__iter__'):
        return tup[j]
    assert j == 0
    return tup


@export.add(('hcurves', 'npz'), ('hmaps', 'npz'), ('uhs', 'npz'),
            ('losses_by_asset', 'npz'), ('damages-rlzs', 'npz'))
def export_hazard_npz(ekey, dstore):
    fname = dstore.export_path('%s.%s' % ekey)
    out = extract(dstore, ekey[0])
    kw = {k: v for k, v in vars(out).items() if not k.startswith('_')}
    savez(fname, **kw)
    return [fname]


@export.add(('gmf_data', 'csv'))
def export_gmf_data_csv(ekey, dstore):
    oq = dstore['oqparam']
    imts = list(oq.imtls)

    # exporting sitemesh
    f = dstore.build_fname('sitemesh', '', 'csv')
    if 'complete' in dstore:
        complete = dstore['complete']
    else:
        complete = dstore['sitecol']
    names = complete.array.dtype.names
    arr = complete[['lon', 'lat']]
    if 'custom_site_id' in names:
        sites = util.compose_arrays(
            complete.custom_site_id, arr, 'custom_site_id')
    else:
        sites = util.compose_arrays(complete.sids, arr, 'site_id')
    writers.write_csv(f, sites, comment=dstore.metadata)

    # exporting gmfs
    df = dstore.read_df('gmf_data').sort_values(['eid', 'sid'])
    if 'custom_site_id' in names:
        df['csi'] = decode(complete.custom_site_id[df.sid])
        ren = {'csi': 'custom_site_id', 'eid': 'event_id'}
        del df['sid']
    else:
        ren = {'sid': 'site_id', 'eid': 'event_id'}
    for m, imt in enumerate(imts):
        ren[f'gmv_{m}'] = 'gmv_' + imt
    for imt in oq.sec_imts:
        ren[imt] = f'sep_{imt}'
    df.rename(columns=ren, inplace=True)
    event_id = dstore['events']['id']
    fname = dstore.build_fname('gmf', 'data', 'csv')
    writers.CsvWriter(fmt=writers.FIVEDIGITS).save(
        df, fname, comment=dstore.metadata)

    # exporting sigma_epsilon
    if 'sigma_epsilon' in dstore['gmf_data']:
        sig_eps_csv = dstore.build_fname('sigma_epsilon', '', 'csv')
        sig_eps = dstore['gmf_data/sigma_epsilon'][()]
        sig_eps['eid'] = event_id[sig_eps['eid']]
        sig_eps.sort(order='eid')
        header = list(sig_eps.dtype.names)
        header[0] = 'event_id'
        writers.write_csv(sig_eps_csv, sig_eps, header=header,
                          comment=dstore.metadata)
        return [fname, sig_eps_csv, f]
    else:
        return [fname, f]


@export.add(('site_model', 'csv'))
def export_site_model_csv(ekey, dstore):
    sitecol = dstore['sitecol']
    fname = dstore.build_fname(ekey[0], '', ekey[1])
    writers.CsvWriter(fmt=writers.FIVEDIGITS).save(
        sitecol.array, fname, comment=dstore.metadata)
    return [fname]



@export.add(('gmf_data', 'hdf5'))
def export_gmf_data_hdf5(ekey, dstore):
    fname = dstore.build_fname('gmf', 'data', 'hdf5')
    with hdf5.File(fname, 'w') as f:
        f['sitecol'] = dstore['sitecol'].complete
        dstore.hdf5.copy('gmf_data', f)
    return [fname]


@export.add(('relevant_gmfs', 'hdf5'))
def export_relevant_gmfs(ekey, dstore):
    oq = dstore['oqparam']
    if oq.number_of_logic_tree_samples == 0:
        raise NotImplementedError('Full enumeration')
    attrs = dstore['gmf_data'].attrs
    fname = dstore.build_fname('gmf', 'data', 'hdf5')
    thr = os.environ.get('OQ_THRESHOLD', '1.')
    with hdf5.File(fname, 'w') as f:
        if dstore.parent:
            f['sitecol'] = dstore.parent['sitecol']
        else:
            f['sitecol'] = dstore['sitecol']
        df = extract(dstore, 'relevant_gmfs?threshold=' + thr)
        f.create_df('gmf_data', df, effective_time=attrs['effective_time'],
                    investigation_time=attrs['investigation_time'],
                    num_events=len(df.eid.unique()),
                    imts=' '.join(oq.imtls))
    return [fname]


@export.add(('avg_gmf', 'csv'))
def export_avg_gmf_csv(ekey, dstore):
    oq = dstore['oqparam']
    if dstore.parent:
        sitecol = dstore.parent['sitecol']
        if 'complete' in dstore.parent:
            sitecol.complete = dstore.parent['complete']
    else:
        sitecol = dstore['sitecol']
        if 'complete' in dstore:
            sitecol.complete = dstore['complete']
    if 'custom_site_id' in sitecol.array.dtype.names:
        dic = dict(custom_site_id=decode(sitecol.complete.custom_site_id))
    else:
        dic = dict(site_id=sitecol.complete.sids)
    dic['lon'] = sitecol.complete.lons
    dic['lat'] = sitecol.complete.lats
    data = dstore['avg_gmf'][:]  # shape (2, N, M)
    for m, imt in enumerate(oq.imtls):
        dic['gmv_' + imt] = data[0, :, m]
        dic['gsd_' + imt] = data[1, :, m]
    fname = dstore.build_fname('avg_gmf', '', 'csv')
    writers.CsvWriter(fmt=writers.FIVEDIGITS).save(
        pandas.DataFrame(dic), fname, comment=dstore.metadata)
    return [fname]


def _expand_gmv(array, imts):
    # the array-field gmv becomes a set of scalar fields gmv_<imt>
    dtype = array.dtype
    assert dtype['gmv'].shape[0] == len(imts)
    dtlist = []
    for name in dtype.names:
        dt = dtype[name]
        if name == 'gmv':
            for imt in imts:
                dtlist.append(('gmv_' + imt, F32))
        elif name in ('sid', 'eid'):
            dtlist.append((name, dt))
        else:  # secondary perils
            dtlist.append((name, dt))
    new = numpy.zeros(len(array), dtlist)
    imti = {imt: i for i, imt in enumerate(imts)}
    for name, _dt in dtlist:
        if name.startswith('gmv_'):
            new[name] = array['gmv'][:, imti[name[4:]]]
        else:
            new[name] = array[name]
    return new


DisaggMatrix = collections.namedtuple(
    'DisaggMatrix', 'poe iml dim_labels matrix')


def iproduct(*sizes):
    ranges = [range(size) for size in sizes]
    return itertools.product(*ranges)


def _add_iml(df, imtls):
    # add field iml and remove field lvl in a dataframe with fields imt, lvl
    out = []
    for imt in imtls:
        imls = imtls[imt]
        dframe = df[df.imt == imt]
        dframe['iml'] = imls[dframe.lvl]
        del dframe['lvl']
        out.append(dframe)
    return pandas.concat(out)


@export.add(('mean_rates_by_src', 'csv'))
def export_mean_rates_by_src(ekey, dstore):
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    rates_df = _add_iml(dstore['mean_rates_by_src'].to_dframe(), oq.imtls)
    fnames = []
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    header = ['source_id', 'imt', 'iml', 'afoe']
    for site in sitecol:
        df = rates_df[rates_df.site_id == site.id]
        del df['site_id']
        df = df[df.value > 0]  # don't export zeros
        df.rename(columns={'src_id': 'source_id',
                           'value': 'afoe'}, inplace=True)
        com = dstore.metadata.copy()
        com['lon'] = round(site.location.x, 5)
        com['lat'] = round(site.location.y, 5)
        com['vs30'] = site.vs30
        fname = dstore.export_path('mean_rates_by_src-%d.csv' % site.id)
        writer.save(df[header].sort_values(header), fname, comment=com)
        fnames.append(fname)
    return fnames


# this exports only the first site and it is okay
@export.add(('mean_disagg_by_src', 'csv'))
def export_mean_disagg_by_src(ekey, dstore):
    sitecol = dstore['sitecol']
    aw = dstore['mean_disagg_by_src']
    df = aw.to_dframe()
    df = df[df.value > 0]  # don't export zeros
    df.rename(columns={'value': 'afoe'}, inplace=True)
    fname = dstore.export_path('%s.%s' % ekey)
    com = dstore.metadata.copy()
    com['lon'] = sitecol.lons[0]
    com['lat'] = sitecol.lats[0]
    com['vs30'] = sitecol.vs30[0]
    com['iml_disagg'] = dict(zip(aw.imt, aw.iml))
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    writer.save(df, fname, comment=com)
    return [fname]


@export.add(('disagg-rlzs', 'csv'),
            ('disagg-stats', 'csv'),
            ('disagg-rlzs-traditional', 'csv'))
def export_disagg_csv(ekey, dstore):
    name, _ext = ekey
    spec = name[7:]  # rlzs, stats, rlzs-traditional, stats-traditional
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    ws = dstore['weights'][:]
    best_rlzs = dstore['best_rlzs'][:]
    N = len(best_rlzs)
    P = len(oq.poes) or 1
    fnames = []
    bins = {name: dset[:] for name, dset in dstore['disagg-bins'].items()}
    ex = 'disagg?kind=%s&site_id=%s&spec=%s'
    trad = '-traditional' if 'traditional' in name else ''
    skip_keys = ('Mag', 'Dist', 'Lon', 'Lat', 'Eps', 'TRT')
    metadata = dstore.metadata
    poes_disagg = ['nan'] * P
    for p in range(P):
        try:
            poes_disagg[p] = str(oq.poes_disagg[p])
        except IndexError:
            pass
    writer = writers.CsvWriter(fmt='%.5E')
    for s in range(N):
        lon, lat = sitecol.lons[s], sitecol.lats[s]
        md = dict(investigation_time=oq.investigation_time,
                  mag_bin_edges=bins['Mag'].tolist(),
                  dist_bin_edges=bins['Dist'].tolist(),
                  lon_bin_edges=bins['Lon'][s].tolist(),
                  lat_bin_edges=bins['Lat'][s].tolist(),
                  eps_bin_edges=bins['Eps'].tolist(),
                  tectonic_region_types=decode(bins['TRT'].tolist()),
                  lon=lon, lat=lat)
        if spec.startswith('rlzs') or oq.iml_disagg:
            weights = ws[best_rlzs[s]]
            weights /= weights.sum()  # normalize to 1
            md['weights'] = weights.tolist()
            md['rlz_ids'] = best_rlzs[s].tolist()
        iml2 = dstore['hmap3'][s]  # shape (M, P)
        metadata.update(md)
        for k in oq.disagg_outputs:
            aw = extract(dstore, ex % (k, s, spec))
            if aw.array.sum() == 0:
                continue
            df = aw.to_dframe(skip_zeros=False)
            # move the columns imt and poe at the beginning for backward compat
            cols = [col for col in df.columns if col not in ('imt', 'poe')]
            # add the IMLs corresponding to the mean hazard maps
            cols = ['imt', 'iml', 'poe'] + cols
            imt2idx = {imt: m for m, imt in enumerate(oq.imtls)}
            poe2idx = {poe: p for p, poe in enumerate(df.poe.unique())}
            imt_idx = [imt2idx[imt] for imt in df.imt]
            poe_idx = [poe2idx[poe] for poe in df.poe]
            df['iml'] = iml2[imt_idx, poe_idx]
            df = pandas.DataFrame(
                {col: df[col] for col in cols}).sort_values(['imt', 'poe'])
            if len(df):
                com = {key: value for key, value in metadata.items()
                       if value is not None and key not in skip_keys}
                com.update(metadata)
                stat = '-mean' if name == 'disagg-stats' else ''
                fname = dstore.export_path(
                    '%s%s%s-%d.csv' % (k, stat, trad, s))
                writer.save(df, fname, comment=com)
                fnames.append(fname)
            else:
                print('Empty file %s not saved', fname)
    return sorted(fnames)


@export.add(('realizations', 'csv'))
def export_realizations(ekey, dstore):
    data = extract(dstore, 'realizations').array
    path = dstore.export_path('realizations.csv')
    writers.write_csv(path, data, fmt='%.7e', comment=dstore.metadata)
    return [path]


@export.add(('events', 'csv'))
def export_events(ekey, dstore):
    events = dstore['events'][()]
    path = dstore.export_path('events.csv')
    writers.write_csv(path, events, fmt='%s', renamedict=dict(id='event_id'),
                      comment=dstore.metadata)
    return [path]


@export.add(('event_based_mfd', 'csv'))
def export_event_based_mfd(ekey, dstore):
    if dstore['oqparam'].investigation_time is None:
        # there is no MFD in scenario calculation
        return []
    aw = extract(dstore, 'event_based_mfd?')
    path = dstore.export_path('event_based_mfd.csv')
    magfreq = numpy.zeros(len(aw.mag), [('mag', float), ('freq', float)])
    magfreq['mag'] = numpy.round(aw.mag, 1)
    magfreq['freq'] = aw.freq
    writers.write_csv(path, magfreq, fmt='%.7e', comment=dstore.metadata)
    return [path]


# because of the code in server.views.calc_results we are not visualizing
# .txt outputs, so we use .rst here
@export.add(('fullreport', 'rst'))
def export_fullreport(ekey, dstore):
    with open(dstore.export_path('report.rst'), 'w') as f:
        f.write(view('fullreport', dstore))
    return [f.name]


@export.add(('rtgm', 'csv'))
def export_rtgm(ekey, dstore):
    df = dstore.read_df('rtgm')
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    fname = dstore.export_path('rtgm.csv')
    comment = dstore.metadata.copy()
    writer.save(df, fname, comment=comment)
    return [fname]

@export.add(('mce', 'csv'))
def export_mce(ekey, dstore):
    df = dstore.read_df('mce')
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    fname = dstore.export_path('mce.csv')
    comment = dstore.metadata.copy()
    writer.save(df, fname, comment=comment)
    return [fname]


@export.add(('asce07', 'csv'), ('asce41', 'csv'))
def export_asce(ekey, dstore):
    sitecol = dstore['sitecol']    
    for s, site in enumerate(sitecol):
        js = dstore[ekey[0]][s].decode('utf8')
        dic = json.loads(js)
        writer = writers.CsvWriter(fmt='%.5f')
        fname = dstore.export_path(ekey[0] + '-' + str(s) + '.csv')
        comment = dstore.metadata.copy()
        comment['lon'] = sitecol.lons[s]
        comment['lat'] = sitecol.lats[s]
        comment['vs30'] = sitecol.vs30[s]
        comment['site_name'] = dstore['oqparam'].description  # e.g. 'CCA example'
        writer.save(dic.items(), fname, header=['parameter', 'value'],
                comment=comment)
    return [fname]


# NB: exporting only the site #0; this is okay
@export.add(('mag_dst_eps_sig', 'csv'))
def export_mag_dst_eps_sig(ekey, dstore):
    data = dstore[ekey[0] + '/0'][:]
    sitecol = dstore['sitecol']
    writer = writers.CsvWriter(fmt='%.5f')
    fname = dstore.export_path('%s.csv' % ekey[0])
    comment = dstore.metadata.copy()
    comment['lon'] = sitecol.lons[0]
    comment['lat'] = sitecol.lats[0]
    comment['vs30'] = sitecol.vs30[0]
    comment['site_name'] = dstore['oqparam'].description  # e.g. 'CCA example'
    writer.save(data, fname, comment=comment)
    return [fname]


@export.add(('trt_gsim', 'csv'))
def export_trt_gsim(ekey, dstore):
    """
    Export a CSV with fields (grp_id, trt, gsim)
    """
    rows = []
    gsims = dstore['gsims'][:]
    data = dstore['source_groups'][:][['grp_id', 'trt', 'gsims']]
    data.sort(order='grp_id')
    g = 0
    for grp_id, trt, G in data:
        for gsim in gsims[g:g + G]:
            rows.append((grp_id, trt, gsim.replace(b'\n', b'\\n')))
        g += G
    fname = dstore.export_path('%s.csv' % ekey[0])
    writer = writers.CsvWriter()
    writer.save(rows, fname, ['grp_id', 'trt', 'gsim'],
                comment=dstore.metadata)
    return [fname]
