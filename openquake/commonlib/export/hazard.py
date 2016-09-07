# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation
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
import pickle
import logging
import operator
import collections

import numpy

from openquake.baselib.general import (
    groupby, humansize, get_array, group_array, DictArray)
from openquake.baselib import hdf5
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.calc import disagg, gmf
from openquake.commonlib.export import export
from openquake.commonlib.writers import write_csv
from openquake.commonlib import writers, hazard_writers, util, readinput
from openquake.risklib.riskinput import create, GmfCollector
from openquake.commonlib import calc

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


def get_mesh(sitecol, complete=True):
    sc = sitecol.complete if complete else sitecol
    mesh = numpy.zeros(len(sc), [('lon', F64), ('lat', F64)])
    mesh['lon'] = sc.lons
    mesh['lat'] = sc.lats
    return mesh


def build_etags(stored_events):
    """
    An array of tags for the underlying seismic events
    """
    tags = []
    for (serial, eid, ses, occ, sampleid, grp_id, source_id) in stored_events:
        tag = b'trt=%02d~ses=%04d~src=%s~rup=%d-%02d' % (
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


@export.add(('sescollection', 'xml'), ('sescollection', 'csv'))
def export_ses_xml(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    fmt = ekey[-1]
    oq = dstore['oqparam']
    mesh = get_mesh(dstore['sitecol'])
    ruptures = []
    for serial in dstore['sescollection']:
        sr = dstore['sescollection/' + serial]
        ruptures.extend(sr.export(mesh))
    ses_coll = SESCollection(
        groupby(ruptures, operator.attrgetter('ses_idx')),
        oq.investigation_time)
    dest = dstore.export_path('ses.' + fmt)
    globals()['_export_ses_' + fmt](dest, ses_coll)
    return [dest]


def _export_ses_xml(dest, ses_coll):
    writer = hazard_writers.SESXMLWriter(dest)
    writer.serialize(ses_coll)


def _export_ses_csv(dest, ses_coll):
    rows = []
    for ses in ses_coll:
        for rup in ses:
            rows.append([rup.etag])
    write_csv(dest, sorted(rows, key=operator.itemgetter(0)))


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
    Convert probability map into a composity array with header
    of the form PGA-0.1, PGA-0.2 ...
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
    write_csv(dest, curves, comment=comment)
    return [dest]


def add_imt(fname, imt):
    """
    >>> add_imt('/path/to/hcurve_23.csv', 'SA(0.1)')
    '/path/to/hcurve-SA(0.1)_23.csv'
    """
    name = os.path.basename(fname)
    newname = re.sub('(_\d+\.)', '-%s\\1' % imt, name)
    return os.path.join(os.path.dirname(fname), newname)


def export_hcurves_by_imt_csv(key, kind, rlzs_assoc, fname, sitecol,
                              curves_by_imt, oq):
    """
    Export the curves of the given realization into CSV.

    :param key: output_type and export_type
    :param kind: a string with the kind of output (realization or statistics)
    :param rlzs_assoc: a :class:`openquake.commonlib.source.RlzsAssoc` instance
    :param fname: name of the exported file
    :param sitecol: site collection
    :param curves_by_imt: dictionary with the curves keyed by IMT
    :param oq: job.ini parameters
    """
    nsites = len(sitecol)
    fnames = []
    for imt, imls in oq.imtls.items():
        dest = add_imt(fname, imt)
        lst = [('lon', F32), ('lat', F32)]
        for iml in imls:
            lst.append((str(iml), F32))
        hcurves = numpy.zeros(nsites, lst)
        for sid, lon, lat in zip(range(nsites), sitecol.lons, sitecol.lats):
            hcurves[sid] = (lon, lat) + tuple(curves_by_imt[sid][imt])
        fnames.append(write_csv(dest, hcurves, comment=_comment(
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
            write_csv(
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


@export.add(('hcurves', 'hdf5'))
def export_hcurves_hdf5(ekey, dstore):
    mesh = get_mesh(dstore['sitecol'])
    imtls = dstore['oqparam'].imtls
    fname = dstore.export_path('%s.%s' % ekey)
    with hdf5.File(fname, 'w') as f:
        f['imtls'] = imtls
        for dskey in dstore[ekey[0]]:
            curves = dstore['%s/%s' % (ekey[0], dskey)].convert(
                imtls, len(mesh))
            f['%s/%s' % (ekey[0], dskey)] = util.compose_arrays(mesh, curves)
    return [fname]


@export.add(('uhs', 'hdf5'))
def export_uhs_hdf5(ekey, dstore):
    oq = dstore['oqparam']
    mesh = get_mesh(dstore['sitecol'])
    fname = dstore.export_path('%s.%s' % ekey)
    with hdf5.File(fname, 'w') as f:
        for dskey in dstore['hcurves']:
            hcurves = dstore['hcurves/%s' % dskey]
            uhs_curves = calc.make_uhs(hcurves, oq.imtls, oq.poes, len(mesh))
            f['uhs/%s' % dskey] = util.compose_arrays(mesh, uhs_curves)
    return [fname]


@export.add(('hmaps', 'hdf5'))
def export_hmaps_hdf5(ekey, dstore):
    oq = dstore['oqparam']
    mesh = get_mesh(dstore['sitecol'])
    pdic = DictArray({imt: oq.poes for imt in oq.imtls})
    fname = dstore.export_path('%s.%s' % ekey)
    with hdf5.File(fname, 'w') as f:
        for dskey in dstore['hcurves']:
            hcurves = dstore['hcurves/%s' % dskey]
            hmap = calc.make_hmap(hcurves, oq.imtls, oq.poes)
            f['hmaps/%s' % dskey] = convert_to_array(hmap, mesh, pdic)
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
    else:
        etags = build_etags(dstore['events'])
    gmf_data = dstore['gmf_data']
    nbytes = gmf_data.attrs['nbytes']
    logging.info('Internal size of the GMFs: %s', humansize(nbytes))
    if nbytes > GMF_MAX_SIZE:
        logging.warn(GMF_WARNING, dstore.hdf5path)
    fnames = []
    for rlz in rlzs_assoc.realizations:
        if n_gmfs:
            # TODO: change to use the prefix rlz-
            gmf_arr = gmf_data['%04d' % rlz.ordinal].value
        else:
            # convert gmf_data in the same format used by scenario
            arrays = []
            for sid in sorted(gmf_data):
                array = get_array(gmf_data[sid].value, rlzi=rlz.ordinal)
                arr = numpy.zeros(len(array), gmv_dt)
                arr['sid'] = int(sid[4:])  # has the form 'sid-XXXX'
                arr['imti'] = array['imti']
                arr['gmv'] = array['gmv']
                arr['eid'] = array['eid']
                arrays.append(arr)
            gmf_arr = numpy.concatenate(arrays)
        ruptures = []
        for eid, gmfa in group_array(gmf_arr, 'eid').items():
            rup = util.Rupture(etags[eid], sorted(set(gmfa['sid'])))
            rup.gmfa = gmfa
            ruptures.append(rup)
        ruptures.sort(key=operator.attrgetter('etag'))
        fname = dstore.build_fname('gmf', rlz, fmt)
        fnames.append(fname)
        globals()['export_gmf_%s' % fmt](
            ('gmf', fmt), fname, sitecol, oq.imtls, ruptures, rlz,
            investigation_time)
    return fnames


@export.add(('gmfs:', 'csv'))
def export_gmf_spec(ekey, dstore, spec):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    :param spec: a string specifying what to export exactly
    """
    oq = dstore['oqparam']
    eids = numpy.array([int(rid) for rid in spec.split(',')])
    sitemesh = get_mesh(dstore['sitecol'])
    writer = writers.CsvWriter(fmt='%.5f')
    if 'scenario' in oq.calculation_mode:
        etags, gmfs_by_trt_gsim = calc.get_gmfs(dstore)
        gsims = sorted(gsim for trt, gsim in gmfs_by_trt_gsim)
        imts = gmfs_by_trt_gsim[0, gsims[0]].dtype.names
        gmf_dt = numpy.dtype([(str(gsim), F32) for gsim in gsims])
        for eid in eids:
            etag = etags[eid]
            for imt in imts:
                gmfa = numpy.zeros(len(sitemesh), gmf_dt)
                for gsim in gsims:
                    gmfa[str(gsim)] = gmfs_by_trt_gsim[0, gsim][imt][:, eid]
                dest = dstore.export_path('gmf-%s-%s.csv' % (etag, imt))
                data = util.compose_arrays(sitemesh, gmfa)
                writer.save(data, dest)
    else:  # event based
        etags = build_etags(dstore['events'])
        for eid in eids:
            etag = etags[eid]
            for gmfa, imt in _calc_gmfs(dstore, util.get_serial(etag), eid):
                dest = dstore.export_path('gmf-%s-%s.csv' % (etag, imt))
                data = util.compose_arrays(sitemesh, gmfa)
                writer.save(data, dest)
    return writer.getsaved()


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
    for rupture in ruptures:
        indices = rupture.indices
        gmvs = [F64(a['gmv'])
                for a in group_array(rupture.gmfa, 'imti').values()]
        row = [rupture.etag, ' '.join(map(str, indices))] + gmvs
        rows.append(row)
    write_csv(dest, rows)
    return {key: [dest]}


def get_rup_idx(ebrup, etag):
    # extract the rupture and the index of the given etag from a collection
    for etag_idx, tag in enumerate(ebrup.etags):
        if tag == etag:
            return etag_idx
    raise ValueError('event tag %s not found in the rupture collection')


def _calc_gmfs(dstore, serial, eid):
    oq = dstore['oqparam']
    min_iml = calc.fix_minimum_intensity(oq.minimum_intensity, oq.imtls)
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    rlzs = rlzs_assoc.realizations
    sitecol = dstore['sitecol'].complete
    N = len(sitecol.complete)
    rup = dstore['sescollection/' + serial]
    correl_model = readinput.get_correl_model(oq)
    rlzs_by_gsim = rlzs_assoc.get_rlzs_by_gsim(rup.grp_id)
    gmf_dt = numpy.dtype([('%03d' % rlz.ordinal, F64)
                          for rlz in rlzs_by_gsim.realizations])
    gmfcoll = create(GmfCollector,
                     [rup], sitecol, list(oq.imtls), rlzs_by_gsim,
                     oq.truncation_level, correl_model, min_iml)
    hazard = {sid: gmfcoll[sid] for sid in gmfcoll.dic}
    for imt in oq.imtls:
        gmfa = numpy.zeros(N, gmf_dt)
        for rlzname in gmf_dt.names:
            rlz = rlzs[int(rlzname)]
            for sid in rup.indices:
                gmvs = hazard[sid][imt][rlz]['gmv']
                gmfa[rlzname][sid] = gmvs
        yield gmfa, imt


@export.add(('gmf_data', 'csv'))
def export_gmf_scenario(ekey, dstore):
    oq = dstore['oqparam']
    if 'scenario' in oq.calculation_mode:
        n_gmfs = oq.number_of_ground_motion_fields
        fields = ['%03d' % i for i in range(n_gmfs)]
        dt = numpy.dtype([(f, F32) for f in fields])
        etags, gmfs_by_trt_gsim = calc.get_gmfs(dstore)
        sitemesh = get_mesh(dstore['sitecol'])
        writer = writers.CsvWriter(fmt='%.5f')
        for (trt, gsim), gmfs_ in gmfs_by_trt_gsim.items():
            for imt in gmfs_.dtype.names:
                gmfs = numpy.zeros(len(gmfs_), dt)
                for i in range(len(gmfs)):
                    gmfs[i] = tuple(gmfs_[imt][i])
                dest = dstore.build_fname('gmf', '%s-%s' % (gsim, imt), 'csv')
                data = util.compose_arrays(sitemesh, gmfs)
                writer.save(data, dest)
    else:  # event based
        logging.warn('Not exporting the full GMFs for event_based, but you can'
                     ' specify the rupture ordinals with gmfs:R1,...,Rn')
        return []
    return writer.getsaved()


@export.add(('gmf_data', 'hdf5'))
def export_gmf_scenario_hdf5(ekey, dstore):
    # compute the GMFs on the fly from the stored rupture (if any)
    oq = dstore['oqparam']
    if 'scenario' not in oq.calculation_mode:
        logging.warn('GMF export not implemented for %s', oq.calculation_mode)
        return []
    sitemesh = get_mesh(dstore['sitecol'], complete=False)
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    gsims = rlzs_assoc.gsims_by_grp_id[0]  # there is a single grp_id
    E = oq.number_of_ground_motion_fields
    correl_model = readinput.get_correl_model(oq)
    computer = gmf.GmfComputer(
            dstore['rupture'], dstore['sitecol'], oq.imtls, gsims,
            oq.truncation_level, correl_model)
    fname = dstore.export_path('%s.%s' % ekey)
    gmf_dt = numpy.dtype([('%s-%03d' % (imt, eid), F32) for imt in oq.imtls
                          for eid in range(E)])
    imts = list(oq.imtls)
    with hdf5.File(fname, 'w') as f:
        for gsim in gsims:
            arr = computer.compute(oq.random_seed, gsim, E)
            I, S, E = arr.shape  # #IMTs, #sites, #events
            gmfa = numpy.zeros(S, gmf_dt)
            for imti in range(I):
                for eid in range(E):
                    field = '%s-%03d' % (imts[imti], eid)
                    gmfa[field] = arr[imti, :, eid]
            f[str(gsim)] = util.compose_arrays(sitemesh, gmfa)
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
        matrix = pickle.loads(group[key].value)
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
        data = [DisaggMatrix(poe, iml, dim_labels, matrix[i])
                for i, dim_labels in enumerate(disagg.pmf_map)]
        writer.serialize(data)
        fnames.append(fname)
    return sorted(fnames)


@export.add(('rup_data', 'csv'))
def export_rup_data(ekey, dstore):
    rupture_data = dstore[ekey[0]]
    paths = []
    for trt in sorted(rupture_data):
        fname = 'rup_data_%s.csv' % trt.lower().replace(' ', '_')
        data = rupture_data[trt].value
        data.sort(order='rupserial')
        if len(data):
            paths.append(write_csv(dstore.export_path(fname), data))
    return paths


@export.add(('realizations', 'csv'))
def export_realizations(ekey, dstore):
    rlzs = dstore[ekey[0]]
    data = [['ordinal', 'uid', 'model', 'gsim', 'weight']]
    for i, rlz in enumerate(rlzs):
        data.append([i, rlz['uid'], rlz['model'], rlz['gsims'], rlz['weight']])
    path = dstore.export_path('realizations.csv')
    writers.write_csv(path, data, fmt='%s')
    return [path]
