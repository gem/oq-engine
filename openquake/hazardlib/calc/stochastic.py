# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2023 GEM Foundation
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

"""
:mod:`openquake.hazardlib.calc.stochastic` contains
:func:`stochastic_event_set`.
"""
import sys
import time
import numpy
from openquake.baselib import hdf5
from openquake.baselib.general import AccumDict
from openquake.baselib.performance import Monitor
from openquake.baselib.python3compat import raise_
from openquake.hazardlib.calc.filters import nofilter, SourceFilter
from openquake.hazardlib.source.rupture import (
    BaseRupture, EBRupture, rupture_dt)
from openquake.hazardlib.geo.mesh import surface_to_arrays

TWO16 = 2 ** 16  # 65,536
TWO32 = 2 ** 32  # 4,294,967,296
F64 = numpy.float64
U16 = numpy.uint16
U32 = numpy.uint32
U8 = numpy.uint8
I32 = numpy.int32
F32 = numpy.float32
MAX_RUPTURES = 2000


# this is used in acceptance/stochastic_test.py, not in the engine
def stochastic_event_set(sources, source_site_filter=nofilter, **kwargs):
    """
    Generates a 'Stochastic Event Set' (that is a collection of earthquake
    ruptures) representing a possible *realization* of the seismicity as
    described by a source model.

    The calculator loops over sources. For each source, it loops over ruptures.
    For each rupture, the number of occurrence is randomly sampled by
    calling
    :meth:`openquake.hazardlib.source.rupture.BaseProbabilisticRupture.sample_number_of_occurrences`

    .. note::
        This calculator is using random numbers. In order to reproduce the
        same results numpy random numbers generator needs to be seeded, see
        http://docs.scipy.org/doc/numpy/reference/generated/numpy.random.seed.html

    :param sources:
        An iterator of seismic sources objects (instances of subclasses
        of :class:`~openquake.hazardlib.source.base.BaseSeismicSource`).
    :param source_site_filter:
        The source filter to use (default noop filter)
    :returns:
        Generator of :class:`~openquake.hazardlib.source.rupture.Rupture`
        objects that are contained in an event set. Some ruptures can be
        missing from it, others can appear one or more times in a row.
    """
    shift_hypo = kwargs['shift_hypo'] if 'shift_hypo' in kwargs else False
    for source, _ in source_site_filter.filter(sources):
        try:
            for rupture in source.iter_ruptures(shift_hypo=shift_hypo):
                [n_occ] = rupture.sample_number_of_occurrences()
                for _ in range(n_occ):
                    yield rupture
        except Exception as err:
            etype, err, tb = sys.exc_info()
            msg = 'An error occurred with source id=%s. Error: %s'
            msg %= (source.source_id, str(err))
            raise_(etype, msg, tb)

# ######################## rupture calculator ############################ #


# this is really fast
def get_rup_array(ebruptures, srcfilter=nofilter):
    """
    Convert a list of EBRuptures into a numpy composite array, by filtering
    out the ruptures far away from every site
    """
    if not BaseRupture._code:
        BaseRupture.init()  # initialize rupture codes

    rups = []
    geoms = []
    for ebrupture in ebruptures:
        rup = ebrupture.rupture
        arrays = surface_to_arrays(rup.surface)  # one array per surface
        lons = []
        lats = []
        points = []
        shapes = []
        for array in arrays:
            s0, s1, s2 = array.shape
            assert s0 == 3, s0
            assert s1 < TWO16, 'Too many lines'
            assert s2 < TWO16, 'The rupture mesh spacing is too small'
            shapes.append(s1)
            shapes.append(s2)
            lons.append(array[0].flat)
            lats.append(array[1].flat)
            points.append(array.flat)
        lons = numpy.concatenate(lons)
        lats = numpy.concatenate(lats)
        points = F32(numpy.concatenate(points))
        shapes = U32(shapes)
        hypo = rup.hypocenter.x, rup.hypocenter.y, rup.hypocenter.z
        rec = numpy.zeros(1, rupture_dt)[0]
        rec['seed'] = rup.seed
        rec['minlon'] = minlon = numpy.nanmin(lons)  # NaNs are in KiteSurfaces
        rec['minlat'] = minlat = numpy.nanmin(lats)
        rec['maxlon'] = maxlon = numpy.nanmax(lons)
        rec['maxlat'] = maxlat = numpy.nanmax(lats)
        rec['mag'] = rup.mag
        rec['hypo'] = hypo
        if srcfilter.sitecol is not None and len(
                srcfilter.close_sids(rec, rup.tectonic_region_type)) == 0:
            continue
        rate = getattr(rup, 'occurrence_rate', numpy.nan)
        tup = (0, ebrupture.seed, ebrupture.source_id, ebrupture.trt_smr,
               rup.code, ebrupture.n_occ, rup.mag, rup.rake, rate,
               minlon, minlat, maxlon, maxlat, hypo, 0, 0)
        rups.append(tup)
        # we are storing the geometries as arrays of 32 bit floating points;
        # the first element is the number of surfaces, then there are
        # 2 * num_surfaces integers describing the first and second
        # dimension of each surface, and then the lons, lats and deps of
        # the underlying meshes of points; in event_based/case_1 there
        # is a point source, i.e. planar surfaces, with shapes = [1, 4]
        # and points.reshape(3, 4) containing lons, lats and depths;
        # in classical/case_29 there is a non parametric source containing
        # 2 KiteSurfaces with shapes=[8, 5, 8, 5] and 240 = 3*2*8*5 coordinates
        # NB: the geometries are read by source.rupture.to_arrays
        geom = numpy.concatenate([[len(shapes) // 2], shapes, points])
        geoms.append(geom)
    if not rups:
        return ()
    dic = dict(geom=numpy.array(geoms, object))
    # NB: PMFs for nonparametric ruptures are not saved since they
    # are useless for the GMF computation
    return hdf5.ArrayWrapper(numpy.array(rups, rupture_dt), dic)


# tested in event_based case_21
def sample_cluster(sources, srcfilter, num_ses, param):
    """
    Yields ruptures generated by a cluster of sources.

    :param sources:
        A sequence of sources of the same group
    :param num_ses:
        Number of stochastic event sets
    :param param:
        a dictionary of additional parameters including
        ses_per_logic_tree_path
    :yields:
        dictionaries with keys rup_array, source_data, eff_ruptures
    """
    eb_ruptures = []
    ses_seed = param['ses_seed']
    numpy.random.seed(sources[0].serial(ses_seed))
    [trt_smr] = set(src.trt_smr for src in sources)
    # AccumDict of arrays with 3 elements nsites, nruptures, calc_time
    source_data = AccumDict(accum=[])
    # Set the parameters required to compute the number of occurrences
    # of the group of sources
    samples = getattr(sources[0], 'samples', 1)
    if getattr(sources, 'src_interdep') == 'mutex':
        # This is the default TOM assigned to a group of mutex sources though
        # it's not necessarily correct. For the time being we keep the current
        # setup since it's ininfluential. We use only the time span.
        # TODO We will need to review this.
        grp_num_occ = samples * num_ses
        threshold_probability = getattr(sources, 'grp_probability')
        if threshold_probability < 1.0:
            vals = numpy.random.rand(grp_num_occ)
            grp_num_occ = sum(vals > threshold_probability)
        srcs_weights = [s.mutex_weight for s in sources]
        srcs_weights.insert(0, 0)
        # Compute the index of the sampled source for each realization
        cs = numpy.cumsum(srcs_weights)
        vals = numpy.random.rand(grp_num_occ)
        sidx = []
        # This provides for each realisation the index of the source sampled
        # according to the weights assigned
        for i_rlz in range(grp_num_occ):
            sidx.append(numpy.max(numpy.where((cs-vals[i_rlz]) < 0)))
    else:
        tom = getattr(sources, 'temporal_occurrence_model')
        rate = tom.occurrence_rate
        time_span = tom.time_span
        # Note that using a single time interval corresponding to the product
        # of the investigation time and the number of realisations as we do
        # here is admitted only in the case of a time-independent model
        grp_num_occ = numpy.random.poisson(rate * time_span * samples *
                                           num_ses)
    # Now we process the sources included in the group. Possible cases:
    # * The group is a cluster. In this case we choose one rupture per each
    #   source; uncertainty in the ruptures can be handled in this case
    #   using mutually exclusive ruptures (note that this is admitted
    #   only for non-parametric sources).
    # * The group contains mutually exclusive sources. In this case we
    #   choose one source and then one rupture from this source.
    rup_counter = {}
    rup_data = {}
    for rlz_num in range(grp_num_occ):
        # In case of a cluster
        if sources.cluster:
            for src, _ in srcfilter.filter(sources):
                # Track calculation time
                t0 = time.time()
                src_id = src.source_id
                rup = src.get_one_rupture(ses_seed)
                # The problem here is that we do not know a-priori the
                # number of occurrences of a given rupture.
                if src_id not in rup_counter:
                    rup_counter[src_id] = {}
                    rup_data[src_id] = {}
                if rup.idx not in rup_counter[src_id]:
                    rup_counter[src_id][rup.idx] = 1
                    rup_data[src_id][rup.idx] = [rup, src_id, trt_smr]
                else:
                    rup_counter[src_id][rup.idx] += 1
                # Store info
                dt = time.time() - t0
                source_data['src_id'].append(src.source_id)
                source_data['nsites'].append(src.nsites)
                source_data['nrups'].append(len(rup_data[src_id]))
                source_data['ctimes'].append(dt)
                source_data['weight'].append(src.weight)
                source_data['taskno'].append(param['task_no'])

        # In case of a set of mutually exclusive sources
        elif getattr(sources, 'src_interdep') == 'mutex':
            # Select the source
            src = sources[sidx[rlz_num]]
            # No ruptures, no party
            if src.count_ruptures() == 0:
                continue
            # Process the ruptures
            for i_rup, rup in enumerate(src.iter_ruptures()):
                rup.idx  # NB: NOT WORKING!
                src_id = src.source_id
                # Create a vector with the probabilities of occurrence of 0, 1,
                # ... n occurrences
                edges = list(rup.probs_occur)
                edges.insert(0, 0.0)
                edges = numpy.array(edges)
                val = numpy.random.rand(1)
                # This is the number of occurrences of the current rupture
                nocc = numpy.max(numpy.where((edges-val) < 0))
                # The problem here is that we do not know a-priori the
                # number of occurrences of a given rupture.
                if src_id not in rup_counter:
                    rup_counter[src_id] = {}
                    rup_data[src_id] = {}
                for _ in range(nocc):
                    if rup.idx not in rup_counter[src_id]:
                        rup_counter[src_id][rup.idx] = 1
                        rup_data[src_id][rup.idx] = [rup, src_id, trt_smr]
                    else:
                        rup_counter[src_id][rup.idx] += 1
                # Store info
                dt = time.time() - t0
                source_data['src_id'].append(src.source_id)
                source_data['nsites'].append(src.nsites)
                source_data['nrups'].append(len(rup_data[src_id]))
                source_data['ctimes'].append(dt)
                source_data['weight'].append(src.weight)
                source_data['taskno'].append(param['task_no'])
        else:
            raise NotImplementedError('Case not supported')

    # Create event based ruptures
    for src_key in rup_data:
        for rup_key in rup_data[src_key]:
            rup, source_id, trt_smr = rup_data[src_key][rup_key]
            cnt = rup_counter[src_key][rup_key]
            ebr = EBRupture(rup, source_id, trt_smr, cnt)
            eb_ruptures.append(ebr)

    return eb_ruptures, source_data


# NB: there is postfiltering of the ruptures, which is more efficient
def sample_ruptures(sources, cmaker, sitecol=None, monitor=Monitor()):
    """
    :param sources:
        a sequence of sources of the same group
    :param cmaker:
        a ContextMaker instance with ses_per_logic_tree_path, ses_seed
    :param sitecol:
        SiteCollection instance used for filtering (None for no filtering)
    :param monitor:
        monitor instance
    :yields:
        dictionaries with keys rup_array, source_data
    """
    srcfilter = SourceFilter(sitecol, cmaker.maximum_distance)
    source_data = AccumDict(accum=[])
    # Compute and save stochastic event sets
    num_ses = cmaker.ses_per_logic_tree_path
    cmaker.task_no = monitor.task_no
    grp_id = sources[0].grp_id
    # Compute the number of occurrences of the source group. This is used
    # for cluster groups or groups with mutually exclusive sources.
    if (getattr(sources, 'atomic', False)):
#            getattr(sources, 'cluster', False)):
        eb_ruptures, source_data = sample_cluster(
            sources, srcfilter, num_ses, vars(cmaker))
        # Yield ruptures
        er = sum(src.num_ruptures for src, _ in srcfilter.filter(sources))
        dic = dict(rup_array=get_rup_array(eb_ruptures, srcfilter),
                   source_data=source_data, eff_ruptures={grp_id: er})
        yield AccumDict(dic)
    else:
        eb_ruptures = []
        eff_ruptures = 0
        source_data = AccumDict(accum=[])
        for src, _ in srcfilter.filter(sources):
            nr = src.num_ruptures
            eff_ruptures += nr
            t0 = time.time()
            if len(eb_ruptures) > MAX_RUPTURES:
                # yield partial result to avoid running out of memory
                yield AccumDict(dict(rup_array=get_rup_array(eb_ruptures,
                                                             srcfilter),
                                     source_data={}, eff_ruptures={}))
                eb_ruptures.clear()
            samples = getattr(src, 'samples', 1)
            for rup, trt_smr, n_occ in src.sample_ruptures(
                    samples * num_ses, cmaker.ses_seed):
                ebr = EBRupture(rup, src.source_id, trt_smr, n_occ)
                eb_ruptures.append(ebr)
            dt = time.time() - t0
            source_data['src_id'].append(src.source_id)
            source_data['nsites'].append(src.nsites)
            source_data['nrups'].append(nr)
            source_data['ctimes'].append(dt)
            source_data['weight'].append(src.weight)
            source_data['taskno'].append(monitor.task_no)
        rup_array = get_rup_array(eb_ruptures, srcfilter)
        yield AccumDict(dict(rup_array=rup_array, source_data=source_data,
                             eff_ruptures={grp_id: eff_ruptures}))
