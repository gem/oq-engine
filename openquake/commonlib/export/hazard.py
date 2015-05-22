#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging
import operator
import collections

import numpy

from openquake.baselib.general import AccumDict, groupby
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.site import FilteredSiteCollection
from openquake.commonlib.export import export
from openquake.commonlib.writers import (
    scientificformat, floatformat, save_csv)
from openquake.commonlib import hazard_writers


class SES(object):
    """
    Stochastic Event Set: A container for 1 or more ruptures associated with a
    specific investigation time span.
    """
    # the ordinal must be > 0: the reason is that it appears in the
    # exported XML file and the schema constraints the number to be
    # nonzero
    def __init__(self, ruptures, investigation_time, ordinal=1):
        self.ruptures = sorted(ruptures, key=operator.attrgetter('tag'))
        self.investigation_time = investigation_time
        self.ordinal = ordinal

    def __iter__(self):
        for sesrup in self.ruptures:
            yield sesrup.export()


class SESCollection(object):
    """
    Stochastic Event Set Collection
    """
    def __init__(self, idx_ses_dict, sm_lt_path, investigation_time=None):
        self.idx_ses_dict = idx_ses_dict
        self.sm_lt_path = sm_lt_path
        self.investigation_time = investigation_time

    def __iter__(self):
        for idx, sesruptures in sorted(self.idx_ses_dict.iteritems()):
            yield SES(sesruptures, self.investigation_time, idx)


@export.add(('sescollection', 'xml'), ('sescollection', 'csv'))
def export_ses_xml(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    fmt = ekey[-1]
    oq = dstore['oqparam']
    try:
        csm_info = dstore['rlzs_assoc'].csm_info
    except AttributeError:  # for scenario calculators don't export
        return []
    sescollection = dstore['sescollection']
    col_id = 0
    fnames = []
    for sm in csm_info.source_models:
        for trt_model in sm.trt_models:
            sesruptures = sescollection[col_id].values()
            col_id += 1
            ses_coll = SESCollection(
                groupby(sesruptures, operator.attrgetter('ses_idx')),
                sm.path, oq.investigation_time)
            smpath = '_'.join(sm.path)
            fname = 'ses-%d-smltp_%s.%s' % (trt_model.id, smpath, fmt)
            dest = os.path.join(dstore.export_dir, fname)
            globals()['_export_ses_' + fmt](dest, ses_coll)
            fnames.append(fname)
    return fnames


def _export_ses_xml(dest, ses_coll):
    writer = hazard_writers.SESXMLWriter(dest, '_'.join(ses_coll.sm_lt_path))
    writer.serialize(ses_coll)


def _export_ses_csv(dest, ses_coll):
    rows = []
    for ses in ses_coll:
        for sesrup in ses:
            rows.append([sesrup.tag, sesrup.seed])
    save_csv(dest, sorted(rows, key=operator.itemgetter(0)))


@export.add(('sitecol', 'csv'))
def export_sitecol_csv(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    dest = dstore.export_path(*ekey)
    rows = []
    for site in dstore['sitecol']:
        rows.append([site.id, site.location.x, site.location.y, site.vs30,
                     site.vs30measured, site.z1pt0, site.z2pt5, site.backarc])
    save_csv(dest, sorted(rows, key=operator.itemgetter(0)))
    return [dest]


# #################### export Ground Motion fields ########################## #

class GmfSet(object):
    """
    Small wrapper around the list of Gmf objects associated to the given SES.
    """
    def __init__(self, gmfset, investigation_time):
        self.gmfset = gmfset
        self.investigation_time = investigation_time
        self.stochastic_event_set_id = 1

    def __iter__(self):
        return iter(self.gmfset)

    def __nonzero__(self):
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
    :rupture_tags: tags of the ruptures
    :gmfs_by_imt: dictionary of GMFs by IMT

    into an object with the right form for the EventBasedGMFXMLWriter.
    Iterating over a GmfCollection yields GmfSet objects.
    """
    def __init__(self, sitecol, ruptures, gmfs, investigation_time):
        self.sitecol = sitecol
        self.ruptures = ruptures
        self.imts = list(gmfs[0].dtype.fields)
        self.gmfs_by_imt = {imt: [gmf[imt] for gmf in gmfs]
                            for imt in self.imts}
        self.investigation_time = investigation_time

    def __iter__(self):
        gmfset = []
        for imt_str in self.imts:
            gmfs = self.gmfs_by_imt[imt_str]
            imt, sa_period, sa_damping = from_string(imt_str)
            for rupture, gmf in zip(self.ruptures, gmfs):
                if hasattr(rupture, 'indices'):  # event based
                    indices = (range(len(self.sitecol))
                               if rupture.indices is None
                               else rupture.indices)
                    sites = FilteredSiteCollection(
                        indices, self.sitecol)
                else:  # scenario
                    sites = self.sitecol
                nodes = (GroundMotionFieldNode(gmv, site.location)
                         for site, gmv in zip(sites, gmf))
                gmfset.append(
                    GroundMotionField(
                        imt, sa_period, sa_damping, rupture.tag, nodes))
        yield GmfSet(gmfset, self.investigation_time)


def export_gmf_xml(key, export_dir, fname, sitecol, ruptures, gmfs, rlz,
                   investigation_time):
    """
    :param key: output_type and export_type
    :param export_dir: the directory where to export
    :param fname: name of the exported file
    :param sitecol: the full site collection
    :param ruptures: an ordered list of ruptures
    :param gmfs: a matrix of ground motion fields of shape (R, N)
    :param rlz: a realization object
    :param investigation_time: investigation time (None for scenario)
    """
    dest = os.path.join(export_dir, fname)
    if hasattr(rlz, 'gsim_rlz'):  # event based
        smltpath = '_'.join(rlz.sm_lt_path)
        gsimpath = rlz.gsim_rlz.uid
    else:  # scenario
        smltpath = ''
        gsimpath = rlz.uid
    writer = hazard_writers.EventBasedGMFXMLWriter(
        dest, sm_lt_path=smltpath, gsim_lt_path=gsimpath)
    with floatformat('%12.8E'):
        writer.serialize(
            GmfCollection(sitecol, ruptures, gmfs, investigation_time))
    return {key: [dest]}


def export_gmf_csv(key, export_dir, fname, sitecol, ruptures, gmfs, rlz,
                   investigation_time):
    """
    :param key: output_type and export_type
    :param export_dir: the directory where to export
    :param fname: name of the exported file
    :param sitecol: the full site collection
    :param ruptures: an ordered list of ruptures
    :param gmfs: an orderd list of ground motion fields
    :param rlz: a realization object
    :param investigation_time: investigation time (None for scenario)
    """
    dest = os.path.join(export_dir, fname)
    imts = list(gmfs[0].dtype.fields)
    # the csv file has the form
    # tag,indices,gmvs_imt_1,...,gmvs_imt_N
    rows = []
    for rupture, gmf in zip(ruptures, gmfs):
        try:
            indices = rupture.indices
        except AttributeError:
            indices = sitecol.indices
        if indices is None:
            indices = range(len(sitecol))
        row = [rupture.tag, ' '.join(map(str, indices))] + \
              [gmf[imt] for imt in imts]
        rows.append(row)
    save_csv(dest, rows)
    return {key: [dest]}

# ####################### export hazard curves ############################ #

HazardCurve = collections.namedtuple('HazardCurve', 'location poes')


def export_hazard_curves_csv(key, export_dir, fname, sitecol, curves_by_imt,
                             imtls, investigation_time=None):
    """
    Export the curves of the given realization into XML.

    :param key: output_type and export_type
    :param export_dir: the directory where to export
    :param fname: name of the exported file
    :param sitecol: site collection
    :param curves_by_imt: dictionary with the curves keyed by IMT
    """
    dest = os.path.join(export_dir, fname)
    nsites = len(sitecol)
    # build a matrix of strings with size nsites * (num_imts + 1)
    # the + 1 is needed since the 0-th column contains lon lat
    rows = numpy.empty((nsites, len(imtls) + 1), dtype=object)
    for sid, lon, lat in zip(range(nsites), sitecol.lons, sitecol.lats):
        rows[sid, 0] = '%s %s' % (lon, lat)
    for i, imt in enumerate(sorted(curves_by_imt.dtype.fields), 1):
        for sid, curve in zip(range(nsites), curves_by_imt[imt]):
            rows[sid, i] = scientificformat(curve, fmt='%11.7E')
    save_csv(dest, rows)
    return {fname: dest}


def hazard_curve_name(ekey, kind, rlzs_assoc, sampling):
    """
    :param ekey: the export key
    :param kind: the kind of key
    :param rlzs_assoc: a RlzsAssoc instance
    :param sampling: if sampling is enabled or not
    """
    key, fmt = ekey
    prefix = {'/hcurves': 'hazard_curve', '/hmaps': 'hazard_map',
              '/uhs': 'hazard_uhs'}[key]
    if kind.startswith('rlz-'):
        rlz_no = int(kind[4:])
        rlz = rlzs_assoc.realizations[rlz_no]
        fname = build_name(rlz, prefix, fmt, sampling)
    elif kind == 'mean':
        fname = '%s-mean.csv' % prefix
    elif kind.startswith('quantile-'):
        # strip the 7 characters 'hazard_'
        fname = 'quantile_%s-%s.%s' % (prefix[7:], kind[9:], fmt)
    else:
        raise ValueError('Unknown kind of hazard curve: %s' % kind)
    return fname


def build_name(rlz, prefix, fmt, sampling):
    """
    Build a file name from a realization, by using prefix and extension.

    :param rlz: a realization object
    :param prefix: the prefix to use
    :param fmt: the extension
    :param bool sampling: if sampling is enabled or not

    :returns: relative pathname including the extension
    """
    if hasattr(rlz, 'sm_lt_path'):  # full realization
        smlt_path = '_'.join(rlz.sm_lt_path)
        suffix = '-ltr_%d' % rlz.ordinal if sampling else ''
        fname = '%s-smltp_%s-gsimltp_%s%s.%s' % (
            prefix, smlt_path, rlz.gsim_rlz.uid, suffix, fmt)
    else:  # GSIM logic tree realization used in scenario calculators
        fname = '%s_%s.%s' % (prefix, rlz.uid, fmt)
    return fname


@export.add(('/hcurves', 'csv'), ('/hmaps', 'csv'), ('/uhs', 'csv'))
def export_hcurves_csv(ekey, dstore):
    """
    Exports the hazard curves into several .csv files

    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    oq = dstore['oqparam']
    rlzs_assoc = dstore['rlzs_assoc']
    sitecol = dstore['sitecol']
    key, fmt = ekey
    fnames = []
    for kind, hcurves in dstore[key].iteritems():
        fname = hazard_curve_name(
            ekey, kind, rlzs_assoc, oq.number_of_logic_tree_samples)
        fnames.append(os.path.join(dstore.export_dir, fname))
        if key == '/uhs':
            export_uhs_csv(ekey, dstore.export_dir, fname, sitecol, hcurves)
        else:
            export_hazard_curves_csv(ekey, dstore.export_dir, fname, sitecol,
                                     hcurves, oq.imtls)
    return fnames


@export.add(('gmf_by_trt_gsim', 'xml'), ('gmf_by_trt_gsim', 'csv'))
def export_gmf(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    sitecol = dstore['sitecol']
    rlzs_assoc = dstore['rlzs_assoc']
    rupture_by_tag = sum(dstore['sescollection'], AccumDict())
    oq = dstore['oqparam']
    samples = oq.number_of_logic_tree_samples
    fmt = ekey[-1]
    fnames = []
    gmf_by_rlz = rlzs_assoc.combine_gmfs(dstore[ekey[0]])
    for rlz, gmf_by_tag in sorted(gmf_by_rlz.iteritems()):
        if isinstance(gmf_by_tag, dict):  # event based
            tags = sorted(gmf_by_tag)
            gmfs = [gmf_by_tag[tag] for tag in tags]
        else:  # scenario calculator, gmf_by_tag is a matrix N x R
            tags = sorted(rupture_by_tag)
            gmfs = gmf_by_tag.T
        ruptures = [rupture_by_tag[tag] for tag in tags]
        fname = build_name(rlz, 'gmf', fmt, samples)
        if len(gmfs) == 0:
            logging.warn('Not generating %s, it would be empty', fname)
            continue
        fnames.append(os.path.join(dstore.export_dir, fname))
        globals()['export_gmf_%s' % fmt](
            ('gmf', fmt), dstore.export_dir, fname, sitecol,
            ruptures, gmfs, rlz, oq.investigation_time)
    return fnames


def export_hazard_curves_xml(key, export_dir, fname, sitecol, curves_by_imt,
                             imtls, investigation_time):
    """
    Export the curves of the given realization into XML.

    :param key: output_type and export_type
    :param export_dir: the directory where to export
    :param fname: name of the exported file
    :param sitecol: site collection
    :param rlz: realization instance
    :param curves_by_imt: dictionary with the curves keyed by IMT
    :param imtls: dictionary with the intensity measure types and levels
    :param investigation_time: investigation time in years
    """
    mdata = []
    hcurves = []
    for imt_str, imls in sorted(imtls.iteritems()):
        hcurves.append(
            [HazardCurve(site.location, poes)
             for site, poes in zip(sitecol, curves_by_imt[imt_str])])
        imt = from_string(imt_str)
        mdata.append({
            'quantile_value': None,
            'statistics': None,
            'smlt_path': '',
            'gsimlt_path': '',
            'investigation_time': investigation_time,
            'imt': imt[0],
            'sa_period': imt[1],
            'sa_damping': imt[2],
            'imls': imls,
        })
    dest = os.path.join(export_dir, fname)
    writer = hazard_writers.MultiHazardCurveXMLWriter(dest, mdata)
    with floatformat('%12.8E'):
        writer.serialize(hcurves)
    return {fname: dest}


def export_stats_csv(key, export_dir, fname, sitecol, data_by_imt):
    """
    Export the scalar outputs.

    :param key: output_type and export_type
    :param export_dir: the directory where to export
    :param fname: file name
    :param sitecol: site collection
    :param data_by_imt: dictionary of floats keyed by IMT
    """
    dest = os.path.join(export_dir, fname)
    rows = []
    for imt in sorted(data_by_imt):
        row = [imt]
        for col in data_by_imt[imt]:
            row.append(scientificformat(col))
        rows.append(row)
    save_csv(dest, numpy.array(rows).T)
    return {fname: dest}


def export_uhs_csv(key, export_dir, fname, sitecol, hmaps):
    """
    Export the scalar outputs.

    :param key: output_type and export_type
    :param export_dir: the directory where to export
    :param fname: file name
    :param sitecol: site collection
    :param hmaps:
        an array N x I x P where N is the number of sites,
        I the number of IMTs of SA type, and P the number of poes
    """
    dest = os.path.join(export_dir, fname)
    rows = ([[lon, lat]] + list(row)
            for lon, lat, row in zip(sitecol.lons, sitecol.lats, hmaps))
    save_csv(dest, rows)
    return {fname: dest}
