# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
import logging
import operator
import collections

import numpy

from openquake.baselib.general import (
    groupby, humansize, get_array, group_array, DictArray)
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.calc import disagg, gmf
from openquake.calculators.export import export
from openquake.commonlib import writers, hazard_writers, calc, util

F32 = numpy.float32
F64 = numpy.float64
U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32

gmv_dt = numpy.dtype([('sid', U16), ('eid', U32), ('imti', U8), ('gmv', F32)])

GMF_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
GMF_WARNING = '''\
There are a lot of ground motion fields; the export will be slow.
Consider canceling the operation and accessing directly %s.'''

# with compression you can save 60% of space by losing only 10% of saving time
savez = numpy.savez_compressed


def get_mesh(sitecol, complete=True):
    sc = sitecol.complete if complete else sitecol
    mesh = numpy.zeros(len(sc), [('lon', F64), ('lat', F64)])
    mesh['lon'] = sc.lons
    mesh['lat'] = sc.lats
    return mesh


def build_etags(events):
    """
    An array of tags for the underlying seismic events
    """
    tags = []
    for (serial, year, ses, occ, sampleid, grp_id, source_id) in events:
        tag = b'grp=%02d~ses=%04d~src=%s~rup=%d-%02d' % (
            grp_id, ses, source_id, serial, occ)
        if sampleid > 0:
            tag += b'~sample=%d' % sampleid
        tags.append(tag)
    return numpy.array(tags)


class SES(object):
    """
    Stochastic Event Set: A container for 1 or more ruptures associated with a
    specific investigation time span.
    """
    # the ordinal must be > 0: the reason is that it appears in the
    # exported XML file and the schema constraints the number to be
    # nonzero
    def __init__(self, ruptures, investigation_time, ordinal=1):
        self.ruptures = sorted(ruptures, key=operator.attrgetter('etag'))
        self.investigation_time = investigation_time
        self.ordinal = ordinal

    def __iter__(self):
        return iter(self.ruptures)


class SESCollection(object):
    """
    Stochastic Event Set Collection
    """
    def __init__(self, idx_ses_dict, investigation_time=None):
        self.idx_ses_dict = idx_ses_dict
        self.investigation_time = investigation_time

    def __iter__(self):
        for idx, sesruptures in sorted(self.idx_ses_dict.items()):
            yield SES(sesruptures, self.investigation_time, idx)


@export.add(('ruptures', 'xml'))
def export_ruptures_xml(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    fmt = ekey[-1]
    oq = dstore['oqparam']
    sm_by_grp = dstore['csm_info'].get_sm_by_grp()
    mesh = get_mesh(dstore['sitecol'])
    ruptures = []
    for grp_id in dstore['ruptures']:
        for serial in dstore['ruptures/%s' % grp_id]:
            sr = dstore['ruptures/%s/%s' % (grp_id, serial)]
            ruptures.extend(sr.export(mesh, sm_by_grp))
    ses_coll = SESCollection(
        groupby(ruptures, operator.attrgetter('ses_idx')),
        oq.investigation_time)
    dest = dstore.export_path('ses.' + fmt)
    writer = hazard_writers.SESXMLWriter(dest)
    writer.serialize(ses_coll)
    return [dest]


@export.add(('ruptures', 'csv'))
def export_ses_csv(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    if 'events' not in dstore:  # scenario
        return []
    dest = dstore.export_path('ruptures.csv')
    header = ('id mag centroid_lon centroid_lat centroid_depth trt '
              'strike dip rake boundary').split()
    csm_info = dstore['csm_info']
    grp_trt = csm_info.grp_trt()
    sm_by_grp = csm_info.get_sm_by_grp()
    rows = []
    for grp_id, trt in sorted(grp_trt.items()):
        sm = 'sm-%04d' % sm_by_grp[grp_id]
        etags = build_etags(dstore['events/' + sm])
        dic = groupby(etags, util.get_serial)
        for r in dstore['rup_data/grp-%02d' % grp_id]:
            for etag in dic[r['rupserial']]:
                boundary = 'MULTIPOLYGON(%s)' % r['boundary']
                rows.append(
                    (etag, r['mag'], r['lon'], r['lat'], r['depth'],
                     trt, r['strike'], r['dip'], r['rake'], boundary))
    rows.sort(key=operator.itemgetter(0))
    writers.write_csv(dest, rows, header=header)
    return [dest]


@export.add(('rup_data', 'csv'))
def export_rup_data(ekey, dstore):
    rupture_data = dstore[ekey[0]]
    paths = []
    for trt in sorted(rupture_data):
        fname = 'rup_data_%s.csv' % trt.lower().replace(' ', '_')
        data = rupture_data[trt].value
        data.sort(order='rupserial')
        if len(data):
            paths.append(writers.write_csv(dstore.export_path(fname), data))
    return paths


# #################### export Ground Motion fields ########################## #

class GmfSet(object):
    """
    Small wrapper around the list of Gmf objects associated to the given SES.
    """
    def __init__(self, gmfset, investigation_time, ses_idx):
        self.gmfset = gmfset
        self.investigation_time = investigation_time
        self.stochastic_event_set_id = ses_idx

    def __iter__(self):
        return iter(self.gmfset)

    def __bool__(self):
        return bool(self.gmfset)

    def __str__(self):
        return (
            'GMFsPerSES(investigation_time=%f, '
            'stochastic_event_set_id=%s,\n%s)' % (
                self.investigation_time,
                self.stochastic_event_set_id, '\n'.join(
                    sorted(str(g) for g in self.gmfset))))


class GroundMotionField(object):
    """
    The Ground Motion Field generated by the given rupture
    """
    def __init__(self, imt, sa_period, sa_damping, rupture_id, gmf_nodes):
        self.imt = imt
        self.sa_period = sa_period
        self.sa_damping = sa_damping
        self.rupture_id = rupture_id
        self.gmf_nodes = gmf_nodes

    def __iter__(self):
        return iter(self.gmf_nodes)

    def __getitem__(self, key):
        return self.gmf_nodes[key]

    def __str__(self):
        # string representation of a _GroundMotionField object showing the
        # content of the nodes (lon, lat an gmv). This is useful for debugging
        # and testing.
        mdata = ('imt=%(imt)s sa_period=%(sa_period)s '
                 'sa_damping=%(sa_damping)s rupture_id=%(rupture_id)s' %
                 vars(self))
        nodes = sorted(map(str, self.gmf_nodes))
        return 'GMF(%s\n%s)' % (mdata, '\n'.join(nodes))


class GroundMotionFieldNode(object):
    # the signature is not (gmv, x, y) because the XML writer expects
    # a location object
    def __init__(self, gmv, loc):
        self.gmv = gmv
        self.location = loc

    def __lt__(self, other):
        """
        A reproducible ordering by lon and lat; used in
        :function:`openquake.commonlib.hazard_writers.gen_gmfs`
        """
        return (self.location.x, self.location.y) < (
            other.location.x, other.location.y)

    def __str__(self):
        """Return lon, lat and gmv of the node in a compact string form"""
        return '<X=%9.5f, Y=%9.5f, GMV=%9.7f>' % (
            self.location.x, self.location.y, self.gmv)


class GmfCollection(object):
    """
    Object converting the parameters

    :param sitecol: SiteCollection
    :param ruptures: ruptures
    :param investigation_time: investigation time

    into an object with the right form for the EventBasedGMFXMLWriter.
    Iterating over a GmfCollection yields GmfSet objects.
    """
    def __init__(self, sitecol, imts, ruptures, investigation_time):
        self.sitecol = sitecol
        self.ruptures = ruptures
        self.imts = imts
        self.investigation_time = investigation_time

    def __iter__(self):
        completemesh = self.sitecol.complete.mesh
        gmfset = collections.defaultdict(list)
        for imti, imt_str in enumerate(self.imts):
            imt, sa_period, sa_damping = from_string(imt_str)
            for rupture in self.ruptures:
                mesh = completemesh[rupture.indices]
                gmf = get_array(rupture.gmfa, imti=imti)['gmv']
                assert len(mesh) == len(gmf), (len(mesh), len(gmf))
                nodes = (GroundMotionFieldNode(gmv, loc)
                         for gmv, loc in zip(gmf, mesh))
                gmfset[rupture.ses_idx].append(
                    GroundMotionField(
                        imt, sa_period, sa_damping, rupture.etag, nodes))
        for ses_idx in sorted(gmfset):
            yield GmfSet(gmfset[ses_idx], self.investigation_time, ses_idx)

# ####################### export hazard curves ############################ #

HazardCurve = collections.namedtuple('HazardCurve', 'location poes')


def convert_to_array(pmap, sitemesh, imtls):
    """
    Convert the probability map into a composite array with header
    of the form PGA-0.1, PGA-0.2 ...

    :param pmap: probability map
    :param sitemesh: mesh of N sites
    :param imtls: a DictArray with IMT and levels
    :returns: a composite array of lenght N
    """
    nsites = len(sitemesh)
    lst = []
    # build the export dtype, of the form PGA-0.1, PGA-0.2 ...
    for imt, imls in imtls.items():
        for iml in imls:
            lst.append(('%s-%s' % (imt, iml), F64))
    curves = numpy.zeros(nsites, numpy.dtype(lst))
    for sid, pcurve in pmap.items():
        curve = curves[sid]
        idx = 0
        for imt, imls in imtls.items():
            for iml in imls:
                curve['%s-%s' % (imt, iml)] = pcurve.array[idx]
                idx += 1
    return util.compose_arrays(sitemesh, curves)


def export_hazard_csv(key, dest, sitemesh, pmap,
                      imtls, comment):
    """
    Export the curves of the given realization into CSV.

    :param key: output_type and export_type
    :param dest: name of the exported file
    :param sitemesh: site collection
    :param pmap: a ProbabilityMap
    :param dict imtls: intensity measure types and levels
    :param comment: comment to use as header of the exported CSV file
    """
    curves = convert_to_array(pmap, sitemesh, imtls)
    writers.write_csv(dest, curves, comment=comment)
    return [dest]


def add_imt(fname, imt):
    """
    >>> add_imt('/path/to/hcurve_23.csv', 'SA(0.1)')
    '/path/to/hcurve-SA(0.1)_23.csv'
    """
    name = os.path.basename(fname)
    newname = re.sub('(_\d+\.)', '-%s\\1' % imt, name)
    return os.path.join(os.path.dirname(fname), newname)


def export_hcurves_by_imt_csv(key, kind, rlzs_assoc, fname, sitecol, pmap, oq):
    """
    Export the curves of the given realization into CSV.

    :param key: output_type and export_type
    :param kind: a string with the kind of output (realization or statistics)
    :param rlzs_assoc: a :class:`openquake.commonlib.source.RlzsAssoc` instance
    :param fname: name of the exported file
    :param sitecol: site collection
    :param pmap: a probability map
    :param oq: job.ini parameters
    """
    nsites = len(sitecol)
    fnames = []
    slicedic = oq.imtls.slicedic
    for imt, imls in oq.imtls.items():
        dest = add_imt(fname, imt)
        lst = [('lon', F32), ('lat', F32)]
        for iml in imls:
            lst.append((str(iml), F32))
        hcurves = numpy.zeros(nsites, lst)
        for sid, lon, lat in zip(range(nsites), sitecol.lons, sitecol.lats):
            poes = pmap.setdefault(sid, 0).array[slicedic[imt]]
            hcurves[sid] = (lon, lat) + tuple(poes)
        fnames.append(writers.write_csv(dest, hcurves, comment=_comment(
            rlzs_assoc, kind, oq.investigation_time) + ',imt=%s' % imt))
    return fnames


def hazard_curve_name(dstore, ekey, kind, rlzs_assoc):
    """
    :param calc_id: the calculation ID
    :param ekey: the export key
    :param kind: the kind of key
    :param rlzs_assoc: a RlzsAssoc instance
    """
    key, fmt = ekey
    prefix = {'hcurves': 'hazard_curve', 'hmaps': 'hazard_map',
              'uhs': 'hazard_uhs'}[key]
    if kind.startswith(('rlz-', 'mean')):
        fname = dstore.build_fname(prefix, kind, fmt)
    elif kind.startswith('quantile-'):
        # strip the 7 characters 'hazard_'
        fname = dstore.build_fname('quantile_' + prefix[7:], kind[9:], fmt)
    else:
        raise ValueError('Unknown kind of hazard curve: %s' % kind)
    return fname


def _comment(rlzs_assoc, kind, investigation_time):
    rlz = rlzs_assoc.get_rlz(kind)
    if not rlz:
        return '%s, investigation_time=%s' % (kind, investigation_time)
    else:
        return (
            'source_model_tree_path=%s,gsim_tree_path=%s,'
            'investigation_time=%s' % (
                rlz.sm_lt_path, rlz.gsim_lt_path, investigation_time))


@export.add(('hcurves', 'csv'), ('hmaps', 'csv'), ('uhs', 'csv'))
def export_hcurves_csv(ekey, dstore):
    """
    Exports the hazard curves into several .csv files

    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    oq = dstore['oqparam']
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    sitecol = dstore['sitecol']
    sitemesh = get_mesh(sitecol)
    key, fmt = ekey
    fnames = []
    if oq.poes:
        pdic = DictArray({imt: oq.poes for imt in oq.imtls})
    for kind in sorted(dstore['hcurves']):
        hcurves = dstore['hcurves/' + kind]
        fname = hazard_curve_name(dstore, ekey, kind, rlzs_assoc)
        comment = _comment(rlzs_assoc, kind, oq.investigation_time)
        if key == 'uhs':
            uhs_curves = calc.make_uhs(
                hcurves, oq.imtls, oq.poes, len(sitemesh))
            writers.write_csv(
                fname, util.compose_arrays(sitemesh, uhs_curves),
                comment=comment)
            fnames.append(fname)
        elif key == 'hmaps':
            hmap = calc.make_hmap(hcurves, oq.imtls, oq.poes)
            fnames.extend(
                export_hazard_csv(ekey, fname, sitemesh, hmap, pdic, comment))
        else:
            if export.from_db:  # called by export_from_db
                fnames.extend(
                    export_hcurves_by_imt_csv(
                        ekey, kind, rlzs_assoc, fname, sitecol, hcurves, oq))
            else:  # when exporting directly from the datastore
                fnames.extend(
                    export_hazard_csv(
                        ekey, fname, sitemesh, hcurves, oq.imtls, comment))

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
    return metadata


@export.add(('uhs', 'xml'))
def export_uhs_xml(ekey, dstore):
    oq = dstore['oqparam']
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    sitemesh = get_mesh(dstore['sitecol'])
    key, fmt = ekey
    fnames = []
    periods = [imt for imt in oq.imtls if imt.startswith('SA') or imt == 'PGA']
    for kind in dstore['hcurves']:
        hcurves = dstore['hcurves/' + kind]
        metadata = get_metadata(rlzs_assoc.realizations, kind)
        _, periods = calc.get_imts_periods(oq.imtls)
        uhs = calc.make_uhs(hcurves, oq.imtls, oq.poes, len(sitemesh))
        for poe in oq.poes:
            fname = hazard_curve_name(
                dstore, ekey, kind + '-%s' % poe, rlzs_assoc)
            writer = hazard_writers.UHSXMLWriter(
                fname, periods=periods, poe=poe,
                investigation_time=oq.investigation_time, **metadata)
            data = []
            for site, curve in zip(sitemesh, uhs[str(poe)]):
                data.append(UHS(curve, Location(site)))
            writer.serialize(data)
            fnames.append(fname)
    return sorted(fnames)


# emulate a Django point
class Location(object):
    def __init__(self, xy):
        self.x, self.y = xy
        self.wkt = 'POINT(%s %s)' % tuple(xy)

HazardCurve = collections.namedtuple('HazardCurve', 'location poes')
HazardMap = collections.namedtuple('HazardMap', 'lon lat iml')


@export.add(('hcurves', 'xml'), ('hcurves', 'geojson'))
def export_hcurves_xml_json(ekey, dstore):
    export_type = ekey[1]
    len_ext = len(export_type) + 1
    oq = dstore['oqparam']
    sitemesh = get_mesh(dstore['sitecol'])
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    hcurves = dstore[ekey[0]]
    fnames = []
    writercls = (hazard_writers.HazardCurveGeoJSONWriter
                 if export_type == 'geojson' else
                 hazard_writers.HazardCurveXMLWriter)
    for kind in hcurves:
        if kind.startswith('rlz-'):
            rlz = rlzs_assoc.realizations[int(kind[4:])]
            smlt_path = '_'.join(rlz.sm_lt_path)
            gsimlt_path = rlz.gsim_rlz.uid
        else:
            smlt_path = ''
            gsimlt_path = ''
        curves = dstore[ekey[0] + '/' + kind].convert(oq.imtls, len(sitemesh))
        name = hazard_curve_name(dstore, ekey, kind, rlzs_assoc)
        for imt in oq.imtls:
            imtype, sa_period, sa_damping = from_string(imt)
            fname = name[:-len_ext] + '-' + imt + '.' + export_type
            data = [HazardCurve(Location(site), poes[imt])
                    for site, poes in zip(sitemesh, curves)]
            writer = writercls(fname,
                               investigation_time=oq.investigation_time,
                               imls=oq.imtls[imt], imt=imtype,
                               sa_period=sa_period, sa_damping=sa_damping,
                               smlt_path=smlt_path, gsimlt_path=gsimlt_path)
            writer.serialize(data)
            fnames.append(fname)
    return sorted(fnames)


@export.add(('hmaps', 'xml'), ('hmaps', 'geojson'))
def export_hmaps_xml_json(ekey, dstore):
    export_type = ekey[1]
    oq = dstore['oqparam']
    sitemesh = get_mesh(dstore['sitecol'])
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    fnames = []
    writercls = (hazard_writers.HazardMapGeoJSONWriter
                 if export_type == 'geojson' else
                 hazard_writers.HazardMapXMLWriter)
    pdic = DictArray({imt: oq.poes for imt in oq.imtls})
    nsites = len(sitemesh)
    for kind in dstore['hcurves']:
        hcurves = dstore['hcurves/' + kind]
        hmaps = calc.make_hmap(
            hcurves, oq.imtls, oq.poes).convert(pdic, nsites)
        if kind.startswith('rlz-'):
            rlz = rlzs_assoc.realizations[int(kind[4:])]
            smlt_path = '_'.join(rlz.sm_lt_path)
            gsimlt_path = rlz.gsim_rlz.uid
        else:
            smlt_path = ''
            gsimlt_path = ''
        for imt in oq.imtls:
            for j, poe in enumerate(oq.poes):
                suffix = '-%s-%s' % (poe, imt)
                fname = hazard_curve_name(
                    dstore, ekey, kind + suffix, rlzs_assoc)
                data = [HazardMap(site[0], site[1], _extract(hmap, imt, j))
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


@export.add(('hcurves', 'npz'))
def export_hcurves_npz(ekey, dstore):
    mesh = get_mesh(dstore['sitecol'])
    imtls = dstore['oqparam'].imtls
    fname = dstore.export_path('%s.%s' % ekey)
    arr = numpy.zeros(1, imtls.dt)
    for imt in imtls:
        arr[imt] = imtls[imt]
    dic = dict(imtls=arr[0])
    for dskey in dstore[ekey[0]]:
        curves = dstore['%s/%s' % (ekey[0], dskey)].convert(
            imtls, len(mesh))
        dic[dskey] = util.compose_arrays(mesh, curves)
    savez(fname, **dic)
    return [fname]


@export.add(('uhs', 'npz'))
def export_uhs_npz(ekey, dstore):
    oq = dstore['oqparam']
    mesh = get_mesh(dstore['sitecol'])
    fname = dstore.export_path('%s.%s' % ekey)
    dic = {}
    for dskey in dstore['hcurves']:
        hcurves = dstore['hcurves/%s' % dskey]
        uhs_curves = calc.make_uhs(hcurves, oq.imtls, oq.poes, len(mesh))
        dic[dskey] = util.compose_arrays(mesh, uhs_curves)
    savez(fname, **dic)
    return [fname]


@export.add(('hmaps', 'npz'))
def export_hmaps_npz(ekey, dstore):
    oq = dstore['oqparam']
    mesh = get_mesh(dstore['sitecol'])
    pdic = DictArray({imt: oq.poes for imt in oq.imtls})
    fname = dstore.export_path('%s.%s' % ekey)
    dic = {}
    for dskey in dstore['hcurves']:
        hcurves = dstore['hcurves/%s' % dskey]
        hmap = calc.make_hmap(hcurves, oq.imtls, oq.poes)
        dic[dskey] = convert_to_array(hmap, mesh, pdic)
    savez(fname, **dic)
    return [fname]


@export.add(('gmf_data', 'xml'), ('gmf_data', 'txt'))
def export_gmf(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    sitecol = dstore['sitecol']
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    oq = dstore['oqparam']
    investigation_time = (None if oq.calculation_mode == 'scenario'
                          else oq.investigation_time)
    fmt = ekey[-1]
    n_gmfs = getattr(oq, 'number_of_ground_motion_fields', None)
    if n_gmfs:
        etags = numpy.array(
            sorted([b'scenario-%010d~ses=1' % i for i in range(n_gmfs)]))
    gmf_data = dstore['gmf_data']
    nbytes = gmf_data.attrs['nbytes']
    logging.info('Internal size of the GMFs: %s', humansize(nbytes))
    if nbytes > GMF_MAX_SIZE:
        logging.warn(GMF_WARNING, dstore.hdf5path)
    fnames = []
    for sm_id, rlzs in sorted(rlzs_assoc.rlzs_by_smodel.items()):
        key = 'sm-%04d' % sm_id
        if not n_gmfs:  # event based
            events = dstore['events']
            if key not in events:  # source model producing zero ruptures
                continue
            etags = build_etags(events[key])
        for rlz in rlzs:
            try:
                gmf_arr = gmf_data['%s/%04d' % (key, rlz.ordinal)].value
            except KeyError:  # no GMFs for the given realization
                continue
            ruptures = []
            for eid, gmfa in group_array(gmf_arr, 'eid').items():
                rup = util.Rupture(sm_id, eid, etags[eid],
                                   sorted(set(gmfa['sid'])))
                rup.gmfa = gmfa
                ruptures.append(rup)
            ruptures.sort(key=operator.attrgetter('etag'))
            fname = dstore.build_fname('gmf', rlz, fmt)
            fnames.append(fname)
            globals()['export_gmf_%s' % fmt](
                ('gmf', fmt), fname, sitecol, oq.imtls, ruptures, rlz,
                investigation_time)
    return fnames


def export_gmf_xml(key, dest, sitecol, imts, ruptures, rlz,
                   investigation_time):
    """
    :param key: output_type and export_type
    :param dest: name of the exported file
    :param sitecol: the full site collection
    :param imts: the list of intensity measure types
    :param ruptures: an ordered list of ruptures
    :param rlz: a realization object
    :param investigation_time: investigation time (None for scenario)
    """
    if hasattr(rlz, 'gsim_rlz'):  # event based
        smltpath = '_'.join(rlz.sm_lt_path)
        gsimpath = rlz.gsim_rlz.uid
    else:  # scenario
        smltpath = ''
        gsimpath = rlz.uid
    writer = hazard_writers.EventBasedGMFXMLWriter(
        dest, sm_lt_path=smltpath, gsim_lt_path=gsimpath)
    writer.serialize(
        GmfCollection(sitecol, imts, ruptures, investigation_time))
    return {key: [dest]}


def export_gmf_txt(key, dest, sitecol, imts, ruptures, rlz,
                   investigation_time):
    """
    :param key: output_type and export_type
    :param dest: name of the exported file
    :param sitecol: the full site collection
    :param imts: the list of intensity measure types
    :param ruptures: an ordered list of ruptures
    :param rlz: a realization object
    :param investigation_time: investigation time (None for scenario)
    """
    # the csv file has the form
    # etag,indices,gmvs_imt_1,...,gmvs_imt_N
    rows = []
    header = ['event_tag', 'site_indices'] + [str(imt) for imt in imts]
    for rupture in ruptures:
        indices = rupture.indices
        gmvs = [F64(a['gmv'])
                for a in group_array(rupture.gmfa, 'imti').values()]
        row = [rupture.etag, ' '.join(map(str, indices))] + gmvs
        rows.append(row)
    writers.write_csv(dest, rows, header=header)
    return {key: [dest]}


def get_sm_id_eid(key):
    """
    Extracts sm_id and eid from the export key.

    >>> get_sm_id_eid('gmf:1:2')
    ['1', '2']
    >>> get_sm_id_eid('gmf:3')
    ['0', '3']
    >>> get_sm_id_eid('gmf')
    [None, None]
    """
    n = key.count(':')
    if n == 1:  # passed the eid, sm_id assumed to be zero
        return ['0', key.split(':')[1]]
    elif n == 2:  # passed both eid and sm_id
        return key.split(':')[1:]
    else:  # eid and sm_id both unspecified, exporting nothing
        return [None, None]


@export.add(('gmf_data', 'csv'))
def export_gmf_data_csv(ekey, dstore):
    oq = dstore['oqparam']
    if 'scenario' in oq.calculation_mode:
        imtls = dstore['oqparam'].imtls
        rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
        gsims = [str(rlz.gsim_rlz) for rlz in rlzs]
        n_gmfs = oq.number_of_ground_motion_fields
        fields = ['%03d' % i for i in range(n_gmfs)]
        dt = numpy.dtype([(f, F32) for f in fields])
        etags, gmfs_ = calc.get_gmfs(dstore)
        sitemesh = get_mesh(dstore['sitecol'])
        writer = writers.CsvWriter(fmt='%.5f')
        for gsim, gmfa in zip(gsims, gmfs_):  # gmfa of shape (N, E)
            for imt in imtls:
                gmfs = numpy.zeros(len(gmfa), dt)
                for i in range(len(gmfa)):
                    gmfs[i] = tuple(gmfa[imt][i])
                dest = dstore.build_fname('gmf', '%s-%s' % (gsim, imt), 'csv')
                data = util.compose_arrays(sitemesh, gmfs)
                writer.save(data, dest)
        return writer.getsaved()
    else:  # event based
        exporter = GmfExporter(dstore)
        sm_id, eid = get_sm_id_eid(ekey[0])
        if eid is None:
            logging.info('Exporting only the first event')
            logging.info('Use the command `oq export gmf_data:*:* %d` '
                         'to export everything', dstore.calc_id)
            return exporter.export_one(0, 0)
        elif eid == '*':
            return exporter.export_all()
        else:
            return exporter.export_one(int(sm_id), int(eid))


class GmfExporter(object):
    def __init__(self, dstore):
        self.dstore = dstore
        self.oq = dstore['oqparam']
        self.rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
        self.sitecol = dstore['sitecol'].complete

    def export_one(self, sm_id, eid):
        fnames = []
        imts = list(self.oq.imtls)
        event = self.dstore['events/sm-%04d' % sm_id][eid]
        [etag] = build_etags([event])
        for rlzno in self.dstore['gmf_data/sm-%04d' % sm_id]:
            rlz = self.rlzs[int(rlzno)]
            gmfa = self.dstore['gmf_data/sm-%04d/%s' % (sm_id, rlzno)]
            gmf = gmfa[gmfa['eid'] == eid]
            data, comment = _build_csv_data(gmf, rlz, self.sitecol, imts,
                                            self.oq.investigation_time)
            fname = self.dstore.build_fname(
                'gmf', '%s-rlz-%03d' % (etag, rlz.ordinal), 'csv')
            logging.info('Exporting %s', fname)
            writers.write_csv(fname, data, comment=comment)
            fnames.append(fname)
        return fnames

    def export_all(self):
        fnames = []
        imts = list(self.oq.imtls)
        for sm_id in self.dstore['gmf_data']:
            events = self.dstore['events/' + sm_id]
            etag = dict(zip(range(len(events)), build_etags(events)))
            for rlzno in self.dstore['gmf_data/' + sm_id]:
                rlz = self.rlzs[int(rlzno)]
                gmf = self.dstore['gmf_data/%s/%s' % (sm_id, rlzno)].value
                for eid, array in group_array(gmf, 'eid').items():
                    data, comment = _build_csv_data(
                        array, rlz, self.sitecol,
                        imts, self.oq.investigation_time)
                    fname = self.dstore.build_fname(
                        'gmf', '%s-rlz-%03d' % (etag[eid], rlz.ordinal), 'csv')
                    logging.info('Exporting %s', fname)
                    writers.write_csv(fname, data, comment=comment)
                    fnames.append(fname)
        return fnames


def _build_csv_data(array, rlz, sitecol, imts, investigation_time):
    # lon, lat, gmv_imt1, ..., gmv_imtN
    smlt_path = '_'.join(rlz.sm_lt_path)
    gsimlt_path = rlz.gsim_rlz.uid
    comment = ('smlt_path=%s, gsimlt_path=%s, investigation_time=%s' %
               (smlt_path, gsimlt_path, investigation_time))
    rows = [['lon', 'lat'] + imts]
    irange = range(len(imts))
    for sid, data in group_array(array, 'sid').items():
        dic = dict(zip(data['imti'], data['gmv']))
        row = ['%.5f' % sitecol.lons[sid], '%.5f' % sitecol.lats[sid]] + [
            dic.get(imti, 0) for imti in irange]
        rows.append(row)
    return rows, comment


@export.add(('gmf_data', 'npz'))
def export_gmf_scenario_npz(ekey, dstore):
    oq = dstore['oqparam']
    dic = {}
    fname = dstore.export_path('%s.%s' % ekey)
    if 'scenario' in oq.calculation_mode:
        # compute the GMFs on the fly from the stored rupture
        sitemesh = get_mesh(dstore['sitecol'], complete=False)
        rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
        gsims = rlzs_assoc.gsims_by_grp_id[0]  # there is a single grp_id
        E = oq.number_of_ground_motion_fields
        correl_model = oq.get_correl_model()
        computer = gmf.GmfComputer(
            dstore['ruptures/grp-00/0'], dstore['sitecol'], oq.imtls,
            gsims, oq.truncation_level, correl_model)
        gmf_dt = numpy.dtype([(imt, (F32, E)) for imt in oq.imtls])
        imts = list(oq.imtls)
        for gsim in gsims:
            arr = computer.compute(gsim, E, oq.random_seed)
            I, S, E = arr.shape  # #IMTs, #sites, #events
            gmfa = numpy.zeros(S, gmf_dt)
            for imti, imt in enumerate(imts):
                gmfa[imt] = arr[imti]
            dic[str(gsim)] = util.compose_arrays(sitemesh, gmfa)
    elif 'gmf_data' in dstore:  # event_based
        for sm_id in sorted(dstore['gmf_data']):
            for rlzno in sorted(dstore['gmf_data/' + sm_id]):
                dic['rlz-' + rlzno] = dstore['gmf_data/%s/%s' % (sm_id, rlzno)]
    else:  # nothing to export
        return []
    savez(fname, **dic)
    return [fname]


DisaggMatrix = collections.namedtuple(
    'DisaggMatrix', 'poe iml dim_labels matrix')


@export.add(('disagg', 'xml'))
def export_disagg_xml(ekey, dstore):
    oq = dstore['oqparam']
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    group = dstore['disagg']
    fnames = []
    writercls = hazard_writers.DisaggXMLWriter
    for key in group:
        matrix = dstore['disagg/' + key]
        attrs = group[key].attrs
        rlz = rlzs[attrs['rlzi']]
        poe = attrs['poe']
        iml = attrs['iml']
        imt, sa_period, sa_damping = from_string(attrs['imt'])
        fname = dstore.export_path(key + '.xml')
        lon, lat = attrs['location']
        # TODO: add poe=poe below
        writer = writercls(
            fname, investigation_time=oq.investigation_time,
            imt=imt, smlt_path='_'.join(rlz.sm_lt_path),
            gsimlt_path=rlz.gsim_rlz.uid, lon=lon, lat=lat,
            sa_period=sa_period, sa_damping=sa_damping,
            mag_bin_edges=attrs['mag_bin_edges'],
            dist_bin_edges=attrs['dist_bin_edges'],
            lon_bin_edges=attrs['lon_bin_edges'],
            lat_bin_edges=attrs['lat_bin_edges'],
            eps_bin_edges=attrs['eps_bin_edges'],
            tectonic_region_types=attrs['trts'],
        )
        data = [
            DisaggMatrix(poe, iml, dim_labels, matrix['_'.join(dim_labels)])
            for i, dim_labels in enumerate(disagg.pmf_map)]
        writer.serialize(data)
        fnames.append(fname)
    return sorted(fnames)


# adapted from the nrml_converters
def save_disagg_to_csv(metadata, matrices):
    """
    Save disaggregation matrices to multiple .csv files.
    """
    skip_keys = ('Mag', 'Dist', 'Lon', 'Lat', 'Eps', 'TRT')
    base_header = ','.join(
        '%s=%s' % (key, value) for key, value in metadata.items()
        if value is not None and key not in skip_keys)

    for disag_type, (poe, iml, matrix, fname) in matrices.items():
        header = '%s,poe=%s,iml=%s\n' % (base_header, poe, iml)

        if disag_type == 'Mag,Lon,Lat':
            matrix = numpy.swapaxes(matrix, 0, 1)
            matrix = numpy.swapaxes(matrix, 1, 2)
            disag_type = 'Lon,Lat,Mag'

        variables = disag_type
        axis = [metadata[v] for v in variables]
        header += ','.join(v for v in variables)
        header += ',poe'

        # compute axis mid points
        axis = [(ax[: -1] + ax[1:]) / 2. if ax.dtype == float
                else ax for ax in axis]

        values = None
        if len(axis) == 1:
            values = numpy.array([axis[0], matrix.flatten()]).T
        else:
            grids = numpy.meshgrid(*axis, indexing='ij')
            values = [g.flatten() for g in grids]
            values.append(matrix.flatten())
            values = numpy.array(values).T

        writers.write_csv(fname, values, comment=header, fmt='%.5E')


@export.add(('disagg', 'csv'))
def export_disagg_csv(ekey, dstore):
    oq = dstore['oqparam']
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    group = dstore['disagg']
    fnames = []
    for key in group:
        matrix = dstore['disagg/' + key]
        attrs = group[key].attrs
        rlz = rlzs[attrs['rlzi']]
        poe = attrs['poe']
        iml = attrs['iml']
        imt, sa_period, sa_damping = from_string(attrs['imt'])
        lon, lat = attrs['location']
        metadata = collections.OrderedDict()
        # Loads "disaggMatrices" nodes
        metadata['smlt_path'] = '_'.join(rlz.sm_lt_path)
        metadata['gsimlt_path'] = rlz.gsim_rlz.uid
        metadata['imt'] = imt
        metadata['investigation_time'] = oq.investigation_time
        metadata['lon'] = lon
        metadata['lat'] = lat
        metadata['Mag'] = attrs['mag_bin_edges']
        metadata['Dist'] = attrs['dist_bin_edges']
        metadata['Lon'] = attrs['lon_bin_edges']
        metadata['Lat'] = attrs['lat_bin_edges']
        metadata['Eps'] = attrs['eps_bin_edges']
        metadata['TRT'] = attrs['trts']
        data = {}
        for dim_labels in disagg.pmf_map:
            label = '_'.join(dim_labels)
            fname = dstore.export_path(key + '_%s.csv' % label)
            data[dim_labels] = poe, iml, matrix[label].value, fname
            fnames.append(fname)
        save_disagg_to_csv(metadata, data)
    return fnames


@export.add(('realizations', 'csv'))
def export_realizations(ekey, dstore):
    rlzs = dstore[ekey[0]]
    data = [['ordinal', 'uid', 'model', 'gsim', 'weight']]
    for i, rlz in enumerate(rlzs):
        data.append([i, rlz['uid'], rlz['model'], rlz['gsims'], rlz['weight']])
    path = dstore.export_path('realizations.csv')
    writers.write_csv(path, data, fmt='%s')
    return [path]
