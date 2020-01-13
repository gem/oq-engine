# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
import operator
import collections
import numpy

from openquake.baselib.general import (
    group_array, deprecated, AccumDict, DictArray)
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.calc import disagg
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
    num_ses = oq.ses_per_logic_tree_path
    ruptures_by_grp = AccumDict(accum=[])
    for rgetter in gen_rupture_getters(dstore):
        ebrs = [ebr.export(rgetter.rlzs_by_gsim, num_ses)
                for ebr in rgetter.get_ruptures()]
        ruptures_by_grp[rgetter.grp_id].extend(ebrs)
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
        key, kind, fname, sitecol, array, imtls, comment):
    """
    Export the curves of the given realization into CSV.

    :param key: output_type and export_type
    :param kind: a string with the kind of output (realization or statistics)
    :param fname: name of the exported file
    :param sitecol: site collection
    :param array: an array of shape (N, L) and dtype numpy.float32
    :param imtls: intensity measure types and levels
    :param comment: comment dictionary
    """
    nsites = len(sitecol)
    fnames = []
    for imt, imls in imtls.items():
        slc = imtls(imt)
        dest = add_imt(fname, imt)
        lst = [('lon', F32), ('lat', F32), ('depth', F32)]
        for iml in imls:
            lst.append(('poe-%.7f' % iml, F32))
        hcurves = numpy.zeros(nsites, lst)
        for sid, lon, lat, dep in zip(
                range(nsites), sitecol.lons, sitecol.lats, sitecol.depths):
            hcurves[sid] = (lon, lat, dep) + tuple(array[sid, slc])
        comment.update(imt=imt)
        fnames.append(
            writers.write_csv(dest, hcurves, comment=comment,
                              header=[name for (name, dt) in lst]))
    return fnames


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
    R = dstore['csm_info'].get_num_rlzs()
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
            hcurves = extract(dstore, 'hcurves?kind=' + kind)[kind]
            if 'amplification' in oq.inputs:
                imtls = DictArray(
                    {imt: oq.soil_intensities for imt in oq.imtls})
            else:
                imtls = oq.imtls
            fnames.extend(
                export_hcurves_by_imt_csv(
                    ekey, kind, fname, sitecol, hcurves, imtls, comment))
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
        metadata['gsimlt_path'] = rlz.gsim_rlz.uid
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
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    R = len(rlzs_assoc.realizations)
    sitemesh = get_mesh(dstore['sitecol'].complete)
    key, kind, fmt = get_kkf(ekey)
    fnames = []
    periods = [imt.period for imt in oq.imt_periods()]
    for kind in oq.get_kinds(kind, R):
        metadata = get_metadata(rlzs_assoc.realizations, kind)
        uhs = extract(dstore, 'uhs?kind=' + kind)[kind]
        for p, poe in enumerate(oq.poes):
            fname = hazard_curve_name(dstore, (key, fmt), kind + '-%s' % poe)
            writer = hazard_writers.UHSXMLWriter(
                fname, periods=periods, poe=poe,
                investigation_time=oq.investigation_time, **metadata)
            data = []
            for site, curve in zip(sitemesh, uhs):
                data.append(UHS(curve[:, p], Location(site)))
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
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    R = len(rlzs_assoc.realizations)
    fnames = []
    writercls = hazard_writers.HazardCurveXMLWriter
    for kind in oq.get_kinds(kind, R):
        if kind.startswith('rlz-'):
            rlz = rlzs_assoc.realizations[int(kind[4:])]
            smlt_path = '_'.join(rlz.sm_lt_path)
            gsimlt_path = rlz.gsim_rlz.uid
        else:
            smlt_path = ''
            gsimlt_path = ''
        name = hazard_curve_name(dstore, ekey, kind)
        hcurves = extract(dstore, 'hcurves?kind=' + kind)[kind]
        for im in oq.imtls:
            slc = oq.imtls(im)
            imt = from_string(im)
            fname = name[:-len_ext] + '-' + im + '.' + fmt
            data = [HazardCurve(Location(site), poes[slc])
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
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    R = len(rlzs_assoc.realizations)
    fnames = []
    writercls = hazard_writers.HazardMapXMLWriter
    for kind in oq.get_kinds(kind, R):
        # shape (N, M, P)
        hmaps = extract(dstore, 'hmaps?kind=' + kind)[kind]
        if kind.startswith('rlz-'):
            rlz = rlzs_assoc.realizations[int(kind[4:])]
            smlt_path = '_'.join(rlz.sm_lt_path)
            gsimlt_path = rlz.gsim_rlz.uid
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
            ('gmf_data', 'npz'),
            ('losses_by_asset', 'npz'), ('dmg_by_asset', 'npz'))
def export_hazard_npz(ekey, dstore):
    fname = dstore.export_path('%s.%s' % ekey)
    out = extract(dstore, ekey[0])
    kw = {k: v for k, v in vars(out).items() if not k.startswith('_')}
    savez(fname, **kw)
    return [fname]


@export.add(('gmf_data', 'csv'))
def export_gmf_data_csv(ekey, dstore):
    oq = dstore['oqparam']
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    imts = list(oq.imtls)
    sc = dstore['sitecol'].array
    arr = sc[['lon', 'lat']]
    eid = int(ekey[0].split('/')[1]) if '/' in ekey[0] else None
    gmfa = dstore['gmf_data/data'][('eid', 'sid', 'gmv')]
    event_id = dstore['events']['id']
    gmfa['eid'] = event_id[gmfa['eid']]
    if eid is None:  # we cannot use extract here
        f = dstore.build_fname('sitemesh', '', 'csv')
        sids = numpy.arange(len(arr), dtype=U32)
        sites = util.compose_arrays(sids, arr, 'site_id')
        writers.write_csv(f, sites)
        fname = dstore.build_fname('gmf', 'data', 'csv')
        gmfa.sort(order=['eid', 'sid'])
        writers.write_csv(fname, _expand_gmv(gmfa, imts),
                          renamedict={'sid': 'site_id', 'eid': 'event_id'})
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
    # old format for single eid
    # TODO: is this still used?
    gmfa = gmfa[gmfa['eid'] == eid]
    eid2rlz = dict(dstore['events'])
    rlzi = eid2rlz[eid]
    rlz = rlzs_assoc.realizations[rlzi]
    data, comment = _build_csv_data(
        gmfa, rlz, dstore['sitecol'], imts, oq.investigation_time)
    fname = dstore.build_fname(
        'gmf', '%d-rlz-%03d' % (eid, rlzi), 'csv')
    return writers.write_csv(fname, data, comment=comment)


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
        else:
            dtlist.append((name, dt))
    new = numpy.zeros(len(array), dtlist)
    for name in dtype.names:
        if name == 'gmv':
            for i, imt in enumerate(imts):
                new['gmv_' + imt] = array['gmv'][:, i]
        else:
            new[name] = array[name]
    return new


def _build_csv_data(array, rlz, sitecol, imts, investigation_time):
    # lon, lat, gmv_imt1, ..., gmv_imtN
    smlt_path = '_'.join(rlz.sm_lt_path)
    gsimlt_path = rlz.gsim_rlz.uid
    comment = ('smlt_path=%s, gsimlt_path=%s, investigation_time=%s' %
               (smlt_path, gsimlt_path, investigation_time))
    rows = [['lon', 'lat'] + imts]
    for sid, data in group_array(array, 'sid').items():
        row = ['%.5f' % sitecol.lons[sid], '%.5f' % sitecol.lats[sid]] + list(
            data['gmv'])
        rows.append(row)
    return rows, comment


DisaggMatrix = collections.namedtuple(
    'DisaggMatrix', 'poe iml dim_labels matrix')


@export.add(('disagg', 'xml'))
@deprecated(msg='Use the CSV exporter instead')
def export_disagg_xml(ekey, dstore):
    oq = dstore['oqparam']
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    group = dstore['disagg']
    fnames = []
    writercls = hazard_writers.DisaggXMLWriter
    trts = dstore.get_attr('csm_info', 'trts')
    for key in group:
        matrix = dstore['disagg/' + key]
        attrs = group[key].attrs
        rlz = rlzs[attrs['rlzi']]
        poe_agg = attrs['poe_agg']
        iml = attrs['iml']
        imt = from_string(attrs['imt'])
        fname = dstore.export_path(key + '.xml')
        lon, lat = attrs['location']
        writer = writercls(
            fname, investigation_time=oq.investigation_time,
            imt=imt.name, smlt_path='_'.join(rlz.sm_lt_path),
            gsimlt_path=rlz.gsim_rlz.uid, lon=lon, lat=lat,
            sa_period=getattr(imt, 'period', None) or None,
            sa_damping=getattr(imt, 'damping', None),
            mag_bin_edges=attrs['mag_bin_edges'],
            dist_bin_edges=attrs['dist_bin_edges'],
            lon_bin_edges=attrs['lon_bin_edges'],
            lat_bin_edges=attrs['lat_bin_edges'],
            eps_bin_edges=attrs['eps_bin_edges'],
            tectonic_region_types=trts)
        data = []
        for poe, k in zip(poe_agg, oq.disagg_outputs or disagg.pmf_map):
            data.append(DisaggMatrix(poe, iml, k.split('_'), matrix[k]))
        writer.serialize(data)
        fnames.append(fname)
    return sorted(fnames)


@export.add(('disagg', 'csv'))
def export_disagg_csv(ekey, dstore):
    oq = dstore['oqparam']
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    group = dstore[ekey[0]]
    fnames = []
    skip_keys = ('Mag', 'Dist', 'Lon', 'Lat', 'Eps', 'TRT')
    for key in group:
        attrs = group[key].attrs
        rlz = rlzs[attrs['rlzi']]
        if not key.startswith('rlz-%d-' % rlz.ordinal):
            continue
        iml = attrs['iml']
        try:
            poe = attrs['poe']
        except Exception:  # no poes_disagg were given
            poe = attrs['poe_agg'][0]
        imt = from_string(attrs['imt'])
        site_id = attrs['site_id']
        lon, lat = attrs['location']
        metadata = dstore.metadata
        # Loads "disaggMatrices" nodes
        if hasattr(rlz, 'sm_lt_path'):
            metadata['smlt_path'] = '_'.join(rlz.sm_lt_path)
            metadata['gsimlt_path'] = rlz.gsim_rlz.uid
        metadata['imt'] = imt.name
        metadata['investigation_time'] = oq.investigation_time
        metadata['lon'] = lon
        metadata['lat'] = lat
        metadata['Mag'] = attrs['mag_bin_edges']
        metadata['Dist'] = attrs['dist_bin_edges']
        metadata['Lon'] = attrs['lon_bin_edges']
        metadata['Lat'] = attrs['lat_bin_edges']
        metadata['Eps'] = attrs['eps_bin_edges']
        metadata['TRT'] = attrs['trt_bin_edges']
        # example: key = 'rlz-0-PGA-sid-0-poe-0'
        poe_id = int(key.rsplit('-', 1)[1])
        for label, dset in sorted(group[key].items()):
            header = label.lower().split('_') + ['poe']
            com = {key: value for key, value in metadata.items()
                   if value is not None and key not in skip_keys}
            com.update(poe='%.7f' % poe, iml='%.7e' % iml, rlz=rlz.ordinal)
            fname = dstore.export_path(key + '_%s.csv' % label)
            values = extract(
                dstore, 'disagg?kind=%s&imt=%s&site_id=%s&poe_id=%d&rlz=%d' %
                (label, imt, site_id, poe_id, rlz.ordinal))
            writers.write_csv(fname, values, header=header, comment=com,
                              fmt='%.5E')
            fnames.append(fname)
    return fnames


@export.add(('disagg_by_src', 'csv'))
def export_disagg_by_src_csv(ekey, dstore):
    paths = []
    srcdata = dstore['disagg_by_grp'][()]
    header = ['source_id', 'poe']
    by_poe = operator.itemgetter(1)
    for name in dstore['disagg_by_src']:
        probs = dstore['disagg_by_src/' + name][()]
        ok = probs > 0
        src = srcdata[ok]
        data = [header] + sorted(zip(add_quotes(src['grp_name']), probs[ok]),
                                 key=by_poe, reverse=True)
        path = dstore.export_path(name + '_Src.csv')
        writers.write_csv(path, data, fmt='%.7e')
        paths.append(path)
    return paths


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
