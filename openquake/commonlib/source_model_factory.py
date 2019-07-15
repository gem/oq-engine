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
import functools
import collections
import logging
import pickle
import zlib
import numpy

from openquake.baselib import hdf5, general, parallel
from openquake.hazardlib import nrml, sourceconverter, sourcewriter, geo
from openquake.hazardlib.geo.mesh import point3d
from openquake.commonlib import logictree

TWO16 = 2 ** 16  # 65,536
source_info_dt = numpy.dtype([
    ('grp_id', numpy.uint16),          # 0
    ('source_id', hdf5.vstr),          # 1
    ('code', (numpy.string_, 1)),      # 2
    ('gidx1', numpy.uint32),           # 3
    ('gidx2', numpy.uint32),           # 4
    ('mfdi', numpy.int32),             # 5
    ('num_ruptures', numpy.uint32),    # 6
    ('calc_time', numpy.float32),      # 7
    ('num_sites', numpy.float32),      # 8
    ('weight', numpy.float32),         # 9
    ('checksum', numpy.uint32),        # 10
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


class SourceModelFactory(object):
    """
    A class able to build source models from the logic tree and to store
    them inside the `source_info` dataset.
    """
    def __init__(self, oqparam, gsim_lt, source_model_lt, monitor,
                 in_memory=True, srcfilter=None):
        self.oqparam = oqparam
        self.gsim_lt = gsim_lt
        self.source_model_lt = source_model_lt
        self.monitor = monitor
        self.hdf5 = monitor.hdf5
        self.in_memory = in_memory
        self.srcfilter = srcfilter
        self.fname_hits = collections.Counter()  # fname -> number of calls
        self.changes = 0
        self.mfds = set()  # set of toml strings
        self.grp_id = 0
        self.source_ids = set()
        self.mags = general.AccumDict(accum=set())  # TRT -> mags

    def __call__(self, fname, sm, apply_uncertainties, investigation_time):
        """
        :param fname:
            the full pathname of a source model file
        :param sm:
            the original source model
        :param apply_uncertainties:
            a function modifying the sources (or None)
        :param investigation_time:
            the investigation_time in the job.ini
        :returns:
            a copy of the original source model with changed sources, if any
        """
        check_nonparametric_sources(fname, sm, investigation_time)
        newsm = nrml.SourceModel(
            [], sm.name, sm.investigation_time, sm.start_time)
        for group in sm:
            newgroup = apply_uncertainties(group)
            newsm.src_groups.append(newgroup)
            if hasattr(newgroup, 'changed') and newgroup.changed.any():
                self.changes += newgroup.changed.sum()
                for src, changed in zip(newgroup, newgroup.changed):
                    # redoing count_ruptures can be slow
                    if changed:
                        src.num_ruptures = src.count_ruptures()
        self.fname_hits[fname] += 1
        return newsm

    def apply_uncertainties(self, sm, idx, dic):
        """
        Apply uncertainties to a source model object and populate
        .source_ids and .mags
        """
        src_groups = []
        apply_unc = functools.partial(
            self.source_model_lt.apply_uncertainties, sm.path)
        smlt_dir = os.path.dirname(self.source_model_lt.filename)
        for name in sm.names.split():
            fname = os.path.abspath(os.path.join(smlt_dir, name))
            if self.in_memory:
                newsm = self(fname, dic[fname], apply_unc,
                             self.oqparam.investigation_time)
                for sg in newsm:
                    # sample a source for each group
                    if os.environ.get('OQ_SAMPLE_SOURCES'):
                        sg.sources = random_filtered_sources(
                            sg.sources, self.srcfilter, sg.id +
                            self.oqparam.random_seed)
                    for src in sg:
                        if hasattr(src, 'data'):  # nonparametric
                            srcmags = [item[0].mag for item in src.data]
                        else:
                            srcmags = [item[0] for item in
                                       src.get_annual_occurrence_rates()]
                        self.mags[src.tectonic_region_type].update(srcmags)
                        self.source_ids.add(src.source_id)
                        src.src_group_id = self.grp_id
                        src.id = idx
                        idx += 1
                    sg.id = self.grp_id
                    self.grp_id += 1
                    src_groups.append(sg)
                if self.hdf5:
                    self.store_sm(newsm)
            else:  # just collect the TRT models
                groups = logictree.read_source_groups(fname)
                for group in groups:
                    self.source_ids.update(src['id'] for src in group)
                src_groups.extend(groups)

        num_sources = sum(len(sg.sources) for sg in src_groups)
        sm.src_groups = src_groups
        trts = [mod.trt for mod in src_groups]
        self.source_model_lt.tectonic_region_types.update(trts)
        logging.info(
            'Processed source model %d with %d gsim path(s) and %d '
            'sources', sm.ordinal + 1, sm.num_gsim_paths, num_sources)

        gsim_file = self.oqparam.inputs.get('gsim_logic_tree')
        if gsim_file:  # check TRTs
            for src_group in src_groups:
                if src_group.trt not in self.gsim_lt.values:
                    raise ValueError(
                        "Found in %r a tectonic region type %r inconsistent "
                        "with the ones in %r" % (sm, src_group.trt, gsim_file))

        if self.grp_id >= TWO16:
            # the limit is really needed only for event based calculations
            raise ValueError('There is a limit of %d src groups!' % TWO16)

        # check applyToSources
        for brid, srcids in self.source_model_lt.info.applytosources.items():
            if brid in sm.path:
                for srcid in srcids:
                    if srcid not in self.source_ids:
                        raise ValueError(
                            'The source %s is not in the source model, please '
                            'fix applyToSources in %s or the source model' %
                            (srcid, self.source_model_lt.filename))

    def store_sm(self, smodel):
        """
        :param smodel: a :class:`openquake.hazardlib.nrml.SourceModel` instance
        """
        h5 = self.hdf5
        sources = h5['source_info']
        source_geom = h5['source_geom']
        gid = len(source_geom)
        for sg in smodel:
            srcs = []
            geoms = []
            for src in sg:
                if hasattr(src, 'mfd'):  # except nonparametric
                    mfdi = len(self.mfds)
                    self.mfds.add(sourcewriter.tomldump(src.mfd))
                else:
                    mfdi = -1
                srcgeom = src.geom()
                n = len(srcgeom)
                geom = numpy.zeros(n, point3d)
                geom['lon'], geom['lat'], geom['depth'] = srcgeom.T
                if len(geom) > 1:  # more than a point source
                    msg = 'source %s' % src.source_id
                    try:
                        geo.utils.check_extent(
                            geom['lon'], geom['lat'], msg)
                    except ValueError as err:
                        logging.error(str(err))
                dic = {k: v for k, v in vars(src).items()
                       if k != 'id' and k != 'src_group_id'}
                src.checksum = zlib.adler32(pickle.dumps(dic))
                srcs.append((sg.id, src.source_id, src.code, gid, gid + n,
                             mfdi, src.num_ruptures, 0, 0, 0,
                             src.checksum))
                geoms.append(geom)
                gid += n
            if geoms:
                hdf5.extend(source_geom, numpy.concatenate(geoms))
            if sources:
                hdf5.extend(sources, numpy.array(srcs, source_info_dt))

    def get_models(self):
        """
        Build all the source models generated by the logic tree.

        :param oqparam:
            an :class:`openquake.commonlib.oqvalidation.OqParam` instance
        :param gsim_lt:
            a :class:`openquake.commonlib.logictree.GsimLogicTree` instance
        :param source_model_lt:
            a :class:`openquake.commonlib.logictree.SourceModelLogicTree` obj
        :param monitor:
            a `openquake.baselib.performance.Monitor` instance
        :param in_memory:
            if True, keep in memory the sources, else just collect the TRTs
        :param srcfilter:
            a SourceFilter iwith a .filename pointing to the cache file
        :returns:
            an iterator over
            :class:`openquake.commonlib.logictree.LtSourceModel` tuples
        """
        oq = self.oqparam
        spinning_off = self.oqparam.pointsource_distance == {'default': 0.0}
        if spinning_off:
            logging.info('Removing nodal plane and hypocenter distributions')
        dist = ('no' if os.environ.get('OQ_DISTRIBUTE') == 'no'
                else 'processpool')
        smlt_dir = os.path.dirname(self.source_model_lt.filename)
        converter = sourceconverter.SourceConverter(
            oq.investigation_time,
            oq.rupture_mesh_spacing,
            oq.complex_fault_mesh_spacing,
            oq.width_of_mfd_bin,
            oq.area_source_discretization,
            oq.minimum_magnitude,
            not spinning_off,
            oq.source_id)
        if oq.calculation_mode.startswith('ucerf'):
            [grp] = nrml.to_python(oq.inputs["source_model"], converter)
            dic = {'ucerf': grp}
        elif self.in_memory:
            logging.info('Reading the source model(s) in parallel')
            smap = parallel.Starmap(
                nrml.read_source_models, monitor=self.monitor, distribute=dist)
            for sm in self.source_model_lt.gen_source_models(self.gsim_lt):
                for name in sm.names.split():
                    fname = os.path.abspath(os.path.join(smlt_dir, name))
                    smap.submit([fname], converter)
            dic = {sm.fname: sm for sm in smap}
        else:
            dic = {}
        # consider only the effective realizations
        idx = 0
        if self.hdf5:
            sources = hdf5.create(self.hdf5, 'source_info', source_info_dt)
            hdf5.create(self.hdf5, 'source_geom', point3d)
            hdf5.create(self.hdf5, 'source_mfds', hdf5.vstr)
        grp_id = 0
        for sm in self.source_model_lt.gen_source_models(self.gsim_lt):
            if 'ucerf' in dic:
                sg = copy.copy(dic['ucerf'])
                sm.src_groups = [sg]
                sg.id = grp_id
                src = sg[0].new(sm.ordinal, sm.names)  # one source
                src.src_group_id = grp_id
                src.id = idx
                if oq.number_of_logic_tree_samples:
                    src.samples = sm.samples
                sg.sources = [src]
                idx += 1
                grp_id += 1
                data = [((sg.id, src.source_id, src.code, 0, 0, -1,
                          src.num_ruptures, 0, 0, 0, idx))]
                hdf5.extend(sources, numpy.array(data, source_info_dt))
            else:
                self.apply_uncertainties(sm, idx, dic)
            yield sm
        if self.mags and self.hdf5:
            mags_by_trt = {trt: sorted(ms) for trt, ms in self.mags.items()}
            idist = self.gsim_lt.get_integration_distance(mags_by_trt, oq)
            self.hdf5['integration_distance'] = idist
            self.hdf5.set_nbytes('integration_distance')
            hdf5.extend(self.hdf5['source_mfds'],
                        numpy.array(list(self.mfds), hdf5.vstr))

        # log if some source file is being used more than once
        dupl = 0
        for fname, hits in self.fname_hits.items():
            if hits > 1:
                logging.info('%s has been considered %d times', fname, hits)
                if not self.changes:
                    dupl += hits
        if self.changes:
            logging.info('Applied %d changes to the composite source model',
                         self.changes)
