# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2019, GEM Foundation
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
import copy
import random
import os.path
import pickle
import functools
import collections
import logging
import zlib
import numpy

from openquake.baselib import hdf5, parallel
from openquake.hazardlib import nrml, sourceconverter, calc

TWO16 = 2 ** 16  # 65,536
source_info_dt = numpy.dtype([
    ('sm_id', numpy.uint16),           # 0
    ('grp_id', numpy.uint16),          # 1
    ('source_id', hdf5.vstr),          # 2
    ('code', (numpy.string_, 1)),      # 3
    ('num_ruptures', numpy.uint32),    # 4
    ('calc_time', numpy.float32),      # 5
    ('num_sites', numpy.float32),      # 6
    ('eff_ruptures', numpy.float32),   # 7
    ('checksum', numpy.uint32),        # 8
    ('wkt', hdf5.vstr),                # 9
])


def random_filtered_sources(sources, srcfilter, seed):
    """
    :param sources: a list of sources
    :param srcfilte: a SourceFilter instance
    :param seed: a random seed
    :returns: an empty list or a list with a single filtered source
    """
    random.seed(seed)
    while sources:
        src = random.choice(sources)
        if srcfilter.get_close_sites(src) is not None:
            return [src]
        sources.remove(src)
    return []


def check_nonparametric_sources(fname, smodel, investigation_time):
    """
    :param fname:
        full path to a source model file
    :param smodel:
        source model object
    :param investigation_time:
        investigation_time to compare with in the case of
        nonparametric sources
    :returns:
        the nonparametric sources in the model
    :raises:
        a ValueError if the investigation_time is different from the expected
    """
    # NonParametricSeismicSources
    np = [src for sg in smodel.src_groups for src in sg
          if hasattr(src, 'data')]
    if np and smodel.investigation_time != investigation_time:
        raise ValueError(
            'The source model %s contains an investigation_time '
            'of %s, while the job.ini has %s' % (
                fname, smodel.investigation_time, investigation_time))
    return np


class SourceReader(object):
    """
    :param converter: a SourceConverter instance
    :param smlt_dir: directory where the source model logic tree file is
    :param h5: if any, HDF5 file with datasets sitecol and oqparam
    """
    def __init__(self, converter, smlt_dir, h5=None):
        self.converter = converter
        self.smlt_dir = smlt_dir
        self.__name__ = 'SourceReader'
        if 'OQ_SAMPLE_SOURCES' in os.environ and h5:
            self.srcfilter = calc.filters.SourceFilter(
                h5['sitecol'], h5['oqparam'].maximum_distance)

    def makesm(self, fname, sm, apply_uncertainties):
        """
        :param fname:
            the full pathname of a source model file
        :param sm:
            the original source model
        :param apply_uncertainties:
            a function modifying the sources (or None)
        :returns:
            a copy of the original source model with changed sources, if any
        """
        check_nonparametric_sources(
            fname, sm, self.converter.investigation_time)
        newsm = nrml.SourceModel(
            [], sm.name, sm.investigation_time, sm.start_time)
        newsm.changes = 0
        for group in sm:
            newgroup = apply_uncertainties(group)
            newsm.src_groups.append(newgroup)
            # the attribute .changed is set by logictree.apply_uncertainties
            if hasattr(newgroup, 'changed') and newgroup.changed.any():
                newsm.changes += newgroup.changed.sum()
                for src, changed in zip(newgroup, newgroup.changed):
                    # redoing count_ruptures can be slow
                    if changed:
                        src.num_ruptures = src.count_ruptures()
        return newsm

    def __call__(self, ltmodel, apply_unc, fname, fileno, monitor):
        fname_hits = collections.Counter()  # fname -> number of calls
        mags = set()
        src_groups = []
        [sm] = nrml.read_source_models([fname], self.converter, monitor)
        newsm = self.makesm(fname, sm, apply_unc)
        fname_hits[fname] += 1
        for sg in newsm:
            # sample a source for each group
            if os.environ.get('OQ_SAMPLE_SOURCES'):
                sg.sources = random_filtered_sources(
                    sg.sources, self.srcfilter, sg.id)
            sg.info = numpy.zeros(len(sg), source_info_dt)
            for i, src in enumerate(sg):
                if hasattr(src, 'data'):  # nonparametric
                    srcmags = ['%.3f' % item[0].mag for item in src.data]
                else:
                    srcmags = ['%.3f' % item[0] for item in
                               src.get_annual_occurrence_rates()]
                mags.update(srcmags)
                dic = {k: v for k, v in vars(src).items()
                       if k != 'id' and k != 'src_group_id'}
                src.checksum = zlib.adler32(
                    pickle.dumps(dic, pickle.HIGHEST_PROTOCOL))
                sg.info[i] = (ltmodel.ordinal, 0, src.source_id,
                              src.code, src.num_ruptures, 0, 0, 0,
                              src.checksum, src.wkt())
            src_groups.append(sg)
        return dict(fname_hits=fname_hits, changes=newsm.changes,
                    src_groups=src_groups, mags=mags,
                    ordinal=ltmodel.ordinal, fileno=fileno)


def get_ltmodels(oq, gsim_lt, source_model_lt, h5=None):
    """
    Build source models from the logic tree and to store
    them inside the `source_info` dataset.
    """
    if oq.pointsource_distance is None:
        spinning_off = False
    else:
        spinning_off = sum(oq.pointsource_distance.values()) == 0
    if spinning_off:
        logging.info('Removing nodal plane and hypocenter distributions')
    # NB: the source models file are often NOT in the shared directory
    # (for instance in oq-engine/demos) so the processpool must be used
    dist = ('no' if os.environ.get('OQ_DISTRIBUTE') == 'no'
            else 'processpool')
    smlt_dir = os.path.dirname(source_model_lt.filename)
    converter = sourceconverter.SourceConverter(
        oq.investigation_time, oq.rupture_mesh_spacing,
        oq.complex_fault_mesh_spacing, oq.width_of_mfd_bin,
        oq.area_source_discretization, oq.minimum_magnitude,
        not spinning_off, oq.source_id)
    if h5:
        sources = hdf5.create(h5, 'source_info', source_info_dt)
    lt_models = list(source_model_lt.gen_source_models(gsim_lt))
    if oq.calculation_mode.startswith('ucerf'):
        idx = 0
        [grp] = nrml.to_python(oq.inputs["source_model"], converter)
        for grp_id, ltm in enumerate(lt_models):
            sg = copy.copy(grp)
            sg.id = grp_id
            ltm.src_groups = [sg]
            src = sg[0].new(ltm.ordinal, ltm.names)  # one source
            src.src_group_id = grp_id
            src.id = idx
            idx += 1
            if oq.number_of_logic_tree_samples:
                src.samples = ltm.samples
            sg.sources = [src]
            data = [((grp_id, grp_id, src.source_id, src.code,
                      0, 0, -1, src.num_ruptures, 0, ''))]
            hdf5.extend(sources, numpy.array(data, source_info_dt))
        return lt_models

    logging.info('Reading the source model(s) in parallel')
    allargs = []
    fileno = 0
    for ltm in lt_models:
        apply_unc = functools.partial(
            source_model_lt.apply_uncertainties, ltm.path)
        for name in ltm.names.split():
            fname = os.path.abspath(os.path.join(smlt_dir, name))
            allargs.append((ltm, apply_unc, fname, fileno))
            fileno += 1
    smap = parallel.Starmap(
        SourceReader(converter, smlt_dir, h5),
        allargs, distribute=dist, h5=h5 if h5 else None)
    # NB: h5 is None in logictree_test.py
    return _store_results(smap, lt_models, source_model_lt, gsim_lt, oq, h5)


def _store_results(smap, lt_models, source_model_lt, gsim_lt, oq, h5):
    mags = set()
    changes = 0
    fname_hits = collections.Counter()
    groups = [[] for _ in lt_models]  # (fileno, src_groups)
    for dic in smap:
        ltm = lt_models[dic['ordinal']]
        groups[ltm.ordinal].append((dic['fileno'], dic['src_groups']))
        fname_hits += dic['fname_hits']
        changes += dic['changes']
        mags.update(dic['mags'])
        gsim_file = oq.inputs.get('gsim_logic_tree')
        if gsim_file:  # check TRTs
            for src_group in dic['src_groups']:
                if src_group.trt not in gsim_lt.values:
                    raise ValueError(
                        "Found in %r a tectonic region type %r "
                        "inconsistent with the ones in %r" %
                        (ltm, src_group.trt, gsim_file))
    # global checks
    idx = 0
    grp_id = 0
    for ltm in lt_models:
        for fileno, grps in sorted(groups[ltm.ordinal]):
            for grp in grps:
                grp.id = grp_id
                for src in grp:
                    src.src_group_id = grp_id
                    src.id = idx
                    idx += 1
                ltm.src_groups.append(grp)
                grp_id += 1
                if grp_id >= TWO16:
                    # the limit is only for event based calculations
                    raise ValueError('There is a limit of %d src groups!' %
                                     TWO16)
        # check applyToSources
        source_ids = set(src.source_id for grp in ltm.src_groups
                         for src in grp)
        for brid, srcids in source_model_lt.info.\
                applytosources.items():
            if brid in ltm.path:
                for srcid in srcids:
                    if srcid not in source_ids:
                        raise ValueError(
                            "The source %s is not in the source model,"
                            " please fix applyToSources in %s or the "
                            "source model" % (
                                srcid, source_model_lt.filename))

        if h5:
            sources = h5['source_info']
            for sg in ltm.src_groups:
                sg.info['grp_id'] = sg.id
                hdf5.extend(sources, sg.info)

    if h5:
        h5['source_mags'] = numpy.array(sorted(mags))

    # log if some source file is being used more than once
    dupl = 0
    for fname, hits in fname_hits.items():
        if hits > 1:
            logging.info('%s has been considered %d times', fname, hits)
            if not changes:
                dupl += hits
    if changes:
        logging.info('Applied %d changes to the composite source model',
                     changes)
    return lt_models
