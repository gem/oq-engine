# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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

from openquake.baselib.general import deprecated, DictArray
from openquake.baselib import hdf5, writers
from openquake.baselib.python3compat import decode
from openquake.hazardlib.imt import from_string
from openquake.calculators.views import view, text_table
from openquake.calculators.extract import extract, get_sites, get_info
from openquake.calculators.export import export
from openquake.commonlib import hazard_writers, calc, util

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


@export.add(('hcurves', 'csv'), ('hmaps', 'csv'), ('uhs', 'csv'))
def export_hcurves_csv(ekey, dstore):
    """
    Exports the hazard curves into several .csv files

    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
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


@deprecated(msg='Use the CSV exporter instead')
def export_uhs_xml(ekey, dstore):
    oq = dstore['oqparam']
    rlzs = dstore['full_lt'].rlzs
    R = len(rlzs)
    sitemesh = get_sites(dstore['sitecol'].complete)
    key, kind, fmt = get_kkf(ekey)
    fnames = []
    periods = [imt.period for imt in oq.imt_periods()]
    for kind in oq.get_kinds(kind, R):
        metadata = get_metadata(rlzs, kind)
        uhs = extract(dstore, 'uhs?kind=' + kind)[kind]
        for p, poe in enumerate(oq.poes):
            fname = hazard_curve_name(dstore, (key, fmt), kind + '-%s' % poe)
            writer = hazard_writers.UHSXMLWriter(
                fname, periods=periods, poe=poe,
                investigation_time=oq.investigation_time, **metadata)
            data = []
            for site, curve in zip(sitemesh, uhs):
                data.append(UHS(curve['%.6f' % poe], Location(site)))
            writer.serialize(data)
            fnames.append(fname)
    return sorted(fnames)


class Location(object):
    def __init__(self, xyz):
        self.x, self.y = xyz['lon'], xyz['lat']
        self.wkt = 'POINT(%s %s)' % (self.x, self.y)


HazardCurve = collections.namedtuple('HazardCurve', 'location poes')
HazardMap = collections.namedtuple('HazardMap', 'lon lat iml')


@deprecated(msg='Use the CSV exporter instead')
def export_hcurves_xml(ekey, dstore):
    key, kind, fmt = get_kkf(ekey)
    len_ext = len(fmt) + 1
    oq = dstore['oqparam']
    sitemesh = get_sites(dstore['sitecol'])
    rlzs = dstore['full_lt'].get_realizations()
    R = len(rlzs)
    fnames = []
    writercls = hazard_writers.HazardCurveXMLWriter
    for kind in oq.get_kinds(kind, R):
        if kind.startswith('rlz-'):
            rlz = rlzs[int(kind[4:])]
            smlt_path = '_'.join(rlz.sm_lt_path)
            gsimlt_path = rlz.gsim_rlz.pid
        else:
            smlt_path = ''
            gsimlt_path = ''
        name = hazard_curve_name(dstore, ekey, kind)
        for im in oq.imtls:
            key = 'hcurves?kind=%s&imt=%s' % (kind, im)
            hcurves = extract(dstore, key)[kind]  # shape (N, 1, L1)
            imt = from_string(im)
            fname = name[:-len_ext] + '-' + im + '.' + fmt
            data = [HazardCurve(Location(site), poes[0])
                    for site, poes in zip(sitemesh, hcurves)]
            imt_name = 'SA' if im.startswith('SA') else im
            writer = writercls(fname,
                               investigation_time=oq.investigation_time,
                               imls=oq.imtls[im], imt=imt_name,
                               sa_period=getattr(imt, 'period', None) or None,
                               sa_damping=getattr(imt, 'damping', None),
                               smlt_path=smlt_path, gsimlt_path=gsimlt_path)
            writer.serialize(data)
            fnames.append(fname)
    return sorted(fnames)


@deprecated(msg='Use the CSV exporter instead')
def export_hmaps_xml(ekey, dstore):
    key, kind, fmt = get_kkf(ekey)
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    sitemesh = get_sites(sitecol)
    rlzs = dstore['full_lt'].get_realizations()
    R = len(rlzs)
    fnames = []
    writercls = hazard_writers.HazardMapXMLWriter
    for kind in oq.get_kinds(kind, R):
        # shape (N, M, P)
        hmaps = extract(dstore, 'hmaps?kind=' + kind)[kind]
        if kind.startswith('rlz-'):
            rlz = rlzs[int(kind[4:])]
            smlt_path = '_'.join(rlz.sm_lt_path)
            gsimlt_path = rlz.gsim_rlz.pid
        else:
            smlt_path = ''
            gsimlt_path = ''
        for m, imt in enumerate(oq.imtls):
            for p, poe in enumerate(oq.poes):
                suffix = '-%s-%s' % (poe, imt)
                fname = hazard_curve_name(dstore, ekey, kind + suffix)
                data = [HazardMap(site[0], site[1], hmap[m, p])
                        for site, hmap in zip(sitemesh, hmaps)]
                writer = writercls(
                    fname, investigation_time=oq.investigation_time,
                    imt=imt, poe=poe,
                    smlt_path=smlt_path, gsimlt_path=gsimlt_path)
                writer.serialize(data)
                fnames.append(fname)
    return sorted(fnames)


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
    sitecol = dstore['sitecol']
    if 'complete' in dstore:
        sitecol.complete = dstore['complete']
    names = sitecol.array.dtype.names
    arr = sitecol[['lon', 'lat']]
    if 'custom_site_id' in names:
        sites = util.compose_arrays(
            sitecol.custom_site_id, arr, 'custom_site_id')
    else:
        sites = util.compose_arrays(sitecol.sids, arr, 'site_id')
    writers.write_csv(f, sites, comment=dstore.metadata)

    # exporting gmfs
    df = dstore.read_df('gmf_data').sort_values(['eid', 'sid'])
    if 'custom_site_id' in names:
        df['csi'] = decode(sitecol.complete.custom_site_id[df.sid])
        ren = {'csi': 'custom_site_id', 'eid': 'event_id'}
        del df['sid']
    else:
        ren = {'sid': 'site_id', 'eid': 'event_id'}
    for m, imt in enumerate(imts):
        ren[f'gmv_{m}'] = 'gmv_' + imt
    for imt in oq.get_sec_imts():
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


@export.add(('gmf_data', 'hdf5'))
def export_gmf_data_hdf5(ekey, dstore):
    fname = dstore.build_fname('gmf', 'data', 'hdf5')
    with hdf5.File(fname, 'w') as f:
        f['sitecol'] = dstore['sitecol'].complete
        dstore.hdf5.copy('gmf_data', f)
    return [fname]


@export.add(('avg_gmf', 'csv'))
def export_avg_gmf_csv(ekey, dstore):
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    if 'complete' in dstore.parent:
        sitecol.complete = dstore.parent['complete']
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
    header = ['src_id', 'imt', 'iml', 'value']
    for site in sitecol:
        df = rates_df[rates_df.site_id == site.id]
        del df['site_id']
        df = df[df.value > 0]  # don't export zeros
        com = dstore.metadata.copy()
        com['lon'] = round(site.location.x, 5)
        com['lat'] = round(site.location.y, 5)
        fname = dstore.export_path('mean_rates_by_src-%d.csv' % site.id)
        writer.save(df[header].sort_values(header), fname, comment=com)
        fnames.append(fname)
    return fnames


@export.add(('mean_disagg_by_src', 'csv'))
def export_mean_disagg_by_src(ekey, dstore):
    sitecol = dstore['sitecol']
    aw = dstore['mean_disagg_by_src']
    df = aw.to_dframe()
    df = df[df.value > 0]  # don't export zeros
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
            ('disagg-rlzs-traditional', 'csv'),
            ('disagg-stats-traditional', 'csv'))
def export_disagg_csv(ekey, dstore):
    name, ext = ekey
    spec = name[7:]  # rlzs, stats, rlzs-traditional, stats-traditional
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    rlzs = dstore['full_lt'].get_realizations()
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
            weights = numpy.array([rlzs[r].weight['weight']
                                   for r in best_rlzs[s]])
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


@export.add(('asce7', 'csv'), ('asce41', 'csv'))
def export_asce(ekey, dstore):
    js = dstore[ekey[0]][()].decode('utf8')
    dic = json.loads(js)
    writer = writers.CsvWriter(fmt='%.5f')
    fname = dstore.export_path('%s.csv' % ekey[0])
    comment = dstore.metadata.copy()
    writer.save(dic.items(), fname, header=['parameter', 'value'],
                comment=comment)
    return [fname]


@export.add(('mag_dst_eps_sig', 'csv'))
def export_mag_dst_eps_sig(ekey, dstore):
    data = dstore[ekey[0]][:]
    writer = writers.CsvWriter(fmt='%.5f')
    fname = dstore.export_path('%s.csv' % ekey[0])
    comment = dstore.metadata.copy()
    writer.save(data, fname, comment=comment)
    return [fname]
