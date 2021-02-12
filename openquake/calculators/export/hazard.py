# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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
import itertools
import collections
import numpy
import pandas

from openquake.baselib.general import (
    group_array, deprecated, AccumDict, DictArray)
from openquake.baselib.python3compat import decode
from openquake.hazardlib.imt import from_string
from openquake.calculators.views import view
from openquake.calculators.extract import extract, get_mesh, get_info
from openquake.calculators.export import export
from openquake.calculators.getters import gen_rupture_getters
from openquake.commonlib import writers, hazard_writers, calc, util

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


@export.add(('ruptures', 'xml'))
@deprecated(msg='This exporter will disappear in the future')
def export_ruptures_xml(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    fmt = ekey[-1]
    oq = dstore['oqparam']
    events = group_array(dstore['events'][()], 'rup_id')
    ruptures_by_grp = AccumDict(accum=[])
    for rgetter in gen_rupture_getters(dstore):
        ebrs = []
        for proxy in rgetter.get_proxies():
            events_by_ses = group_array(events[proxy['id']], 'ses_id')
            ebr = proxy.to_ebr(rgetter.trt)
            ebrs.append(ebr.export(events_by_ses))
        ruptures_by_grp[rgetter.et_id].extend(ebrs)
    dest = dstore.export_path('ses.' + fmt)
    writer = hazard_writers.SESXMLWriter(dest)
    writer.serialize(ruptures_by_grp, oq.investigation_time)
    return [dest]


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
        if bad.count('\n') > 3:  # nonempty rst_table
            print(bad, file=sys.stderr)
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
    >>> add_imt('/path/to/hcurve_23.csv', 'SA(0.1)')
    '/path/to/hcurve-SA(0.1)_23.csv'
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
    R = dstore['full_lt'].get_num_rlzs()
    sitecol = dstore['sitecol']
    sitemesh = get_mesh(sitecol)
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


def get_metadata(realizations, kind):
    """
    :param list realizations:
        realization objects
    :param str kind:
        kind of data, i.e. a key in the datastore
    :returns:
        a dictionary with smlt_path, gsimlt_path, statistics, quantile_value
    """
    metadata = {}
    if kind.startswith('rlz-'):
        rlz = realizations[int(kind[4:])]
        metadata['smlt_path'] = '_'.join(rlz.sm_lt_path)
        metadata['gsimlt_path'] = rlz.gsim_rlz.pid
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


@export.add(('uhs', 'xml'))
@deprecated(msg='Use the CSV exporter instead')
def export_uhs_xml(ekey, dstore):
    oq = dstore['oqparam']
    rlzs = dstore['full_lt'].get_realizations()
    R = len(rlzs)
    sitemesh = get_mesh(dstore['sitecol'].complete)
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
                data.append(UHS(curve[str(poe)], Location(site)))
            writer.serialize(data)
            fnames.append(fname)
    return sorted(fnames)


class Location(object):
    def __init__(self, xyz):
        self.x, self.y = tuple(xyz)[:2]
        self.wkt = 'POINT(%s %s)' % (self.x, self.y)


HazardCurve = collections.namedtuple('HazardCurve', 'location poes')
HazardMap = collections.namedtuple('HazardMap', 'lon lat iml')


@export.add(('hcurves', 'xml'))
@deprecated(msg='Use the CSV exporter instead')
def export_hcurves_xml(ekey, dstore):
    key, kind, fmt = get_kkf(ekey)
    len_ext = len(fmt) + 1
    oq = dstore['oqparam']
    sitemesh = get_mesh(dstore['sitecol'])
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
            writer = writercls(fname,
                               investigation_time=oq.investigation_time,
                               imls=oq.imtls[im], imt=imt.name,
                               sa_period=getattr(imt, 'period', None) or None,
                               sa_damping=getattr(imt, 'damping', None),
                               smlt_path=smlt_path, gsimlt_path=gsimlt_path)
            writer.serialize(data)
            fnames.append(fname)
    return sorted(fnames)


@export.add(('hmaps', 'xml'))
@deprecated(msg='Use the CSV exporter instead')
def export_hmaps_xml(ekey, dstore):
    key, kind, fmt = get_kkf(ekey)
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    sitemesh = get_mesh(sitecol)
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
    df = dstore.read_df('gmf_data').sort_values(['eid', 'sid'])
    ren = {'sid': 'site_id', 'eid': 'event_id'}
    for m, imt in enumerate(imts):
        ren[f'gmv_{m}'] = 'gmv_' + imt
    for imt in oq.get_sec_imts():
        ren[imt] = f'sep_{imt}'
    df.rename(columns=ren, inplace=True)
    event_id = dstore['events']['id']
    f = dstore.build_fname('sitemesh', '', 'csv')
    arr = dstore['sitecol'][['lon', 'lat']]
    sids = numpy.arange(len(arr), dtype=U32)
    sites = util.compose_arrays(sids, arr, 'site_id')
    writers.write_csv(f, sites)
    fname = dstore.build_fname('gmf', 'data', 'csv')
    writers.CsvWriter(fmt=writers.FIVEDIGITS).save(
        df, fname, comment=dstore.metadata)
    if 'sigma_epsilon' in dstore['gmf_data']:
        sig_eps_csv = dstore.build_fname('sigma_epsilon', '', 'csv')
        sig_eps = dstore['gmf_data/sigma_epsilon'][()]
        sig_eps['eid'] = event_id[sig_eps['eid']]
        sig_eps.sort(order='eid')
        header = list(sig_eps.dtype.names)
        header[0] = 'event_id'
        writers.write_csv(sig_eps_csv, sig_eps, header=header)
        return [fname, sig_eps_csv, f]
    else:
        return [fname, f]


@export.add(('avg_gmf', 'csv'))
def export_avg_gmf_csv(ekey, dstore):
    oq = dstore['oqparam']
    sitecol = dstore['sitecol'].complete
    data = dstore['avg_gmf'][:]  # shape (2, N, M)
    dic = {'site_id': sitecol.sids, 'lon': sitecol.lons, 'lat': sitecol.lats}
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


@export.add(('disagg', 'csv'), ('disagg', 'xml'))
def export_disagg_csv_xml(ekey, dstore):
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    hmap4 = dstore['hmap4']
    N, M, P, Z = hmap4.shape
    imts = list(oq.imtls)
    rlzs = dstore['full_lt'].get_realizations()
    fnames = []
    writercls = hazard_writers.DisaggXMLWriter
    bins = {name: dset[:] for name, dset in dstore['disagg-bins'].items()}
    ex = 'disagg?kind=%s&imt=%s&site_id=%s&poe_id=%d&z=%d'
    skip_keys = ('Mag', 'Dist', 'Lon', 'Lat', 'Eps', 'TRT')
    for s, m, p, z in iproduct(N, M, P, Z):
        dic = {k: dstore['disagg/' + k][s, m, p, ..., z]
               for k in oq.disagg_outputs}
        if sum(arr.sum() for arr in dic.values()) == 0:  # no data
            continue
        imt = from_string(imts[m])
        r = hmap4.rlzs[s, z]
        rlz = rlzs[r]
        iml = hmap4[s, m, p, z]
        poe_agg = dstore['poe4'][s, m, p, z]
        fname = dstore.export_path(
            'rlz-%d-%s-sid-%d-poe-%d.xml' % (r, imt, s, p))
        lon, lat = sitecol.lons[s], sitecol.lats[s]
        metadata = dstore.metadata
        metadata.update(investigation_time=oq.investigation_time,
                        imt=imt.name,
                        smlt_path='_'.join(rlz.sm_lt_path),
                        gsimlt_path=rlz.gsim_rlz.pid, lon=lon, lat=lat,
                        mag_bin_edges=bins['Mag'].tolist(),
                        dist_bin_edges=bins['Dist'].tolist(),
                        lon_bin_edges=bins['Lon'][s].tolist(),
                        lat_bin_edges=bins['Lat'][s].tolist(),
                        eps_bin_edges=bins['Eps'].tolist(),
                        tectonic_region_types=decode(bins['TRT'].tolist()))
        if ekey[1] == 'xml':
            metadata['sa_period'] = getattr(imt, 'period', None) or None
            metadata['sa_damping'] = getattr(imt, 'damping', None)
            writer = writercls(fname, **metadata)
            data = []
            for k in oq.disagg_outputs:
                data.append(DisaggMatrix(poe_agg, iml, k.split('_'), dic[k]))
            writer.serialize(data)
            fnames.append(fname)
        else:  # csv
            metadata['poe'] = poe_agg
            for k in oq.disagg_outputs:
                header = k.lower().split('_') + ['poe']
                com = {key: value for key, value in metadata.items()
                       if value is not None and key not in skip_keys}
                com.update(metadata)
                fname = dstore.export_path(
                    'rlz-%d-%s-sid-%d-poe-%d_%s.csv' % (r, imt, s, p, k))
                values = extract(dstore, ex % (k, imt, s, p, z))
                writers.write_csv(fname, values, header=header,
                                  comment=com, fmt='%.5E')
                fnames.append(fname)
    return sorted(fnames)


@export.add(('realizations', 'csv'))
def export_realizations(ekey, dstore):
    data = extract(dstore, 'realizations').array
    path = dstore.export_path('realizations.csv')
    writers.write_csv(path, data, fmt='%.7e')
    return [path]


@export.add(('events', 'csv'))
def export_events(ekey, dstore):
    events = dstore['events'][()]
    path = dstore.export_path('events.csv')
    writers.write_csv(path, events, fmt='%s', renamedict=dict(id='event_id'))
    return [path]


# because of the code in server.views.calc_results we are not visualizing
# .txt outputs, so we use .rst here
@export.add(('fullreport', 'rst'))
def export_fullreport(ekey, dstore):
    with open(dstore.export_path('report.rst'), 'w') as f:
        f.write(view('fullreport', dstore))
    return [f.name]
