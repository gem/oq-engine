# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2021 GEM Foundation
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
from openquake.hazardlib.calc.filters import nofilter
from openquake.hazardlib.source.rupture import BaseRupture, EBRupture
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

rupture_dt = numpy.dtype([
    ('id', U32), ('seed', U32), ('source_id', '<S16'), ('et_id', U16),
    ('code', U8), ('n_occ', U32), ('mag', F32), ('rake', F32),
    ('occurrence_rate', F32),
    ('minlon', F32), ('minlat', F32), ('maxlon', F32), ('maxlat', F32),
    ('hypo', (F32, 3)), ('geom_id', U32), ('e0', U32), ('e1', U32)])


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
        arrays = surface_to_arrays(rup.surface)
        points = []
        shapes = []
        for array in arrays:
            s0, s1, s2 = array.shape
            assert s0 == 3, s0
            assert s1 < TWO16, 'Too many lines'
            assert s2 < TWO16, 'The rupture mesh spacing is too small'
            shapes.append(s1)
            shapes.append(s2)
            points.extend(array.flat)
            # example of points: [25.0, 25.1, 25.1, 25.0,
            #                     -24.0, -24.0, -24.1, -24.1,
            #                      5.0, 5.0, 5.0, 5.0]
        points = F32(points)
        shapes = U32(shapes)
        hypo = rup.hypocenter.x, rup.hypocenter.y, rup.hypocenter.z
        rec = numpy.zeros(1, rupture_dt)[0]
        rec['seed'] = rup.rup_id
        n = len(points) // 3
        lons = points[0:n]
        lats = points[n:2*n]
        rec['minlon'] = minlon = lons.min()
        rec['minlat'] = minlat = lats.min()
        rec['maxlon'] = maxlon = lons.max()
        rec['maxlat'] = maxlat = lats.max()
        rec['mag'] = rup.mag
        rec['hypo'] = hypo
        if srcfilter.integration_distance and len(
                srcfilter.close_sids(rec, rup.tectonic_region_type)) == 0:
            continue
        rate = getattr(rup, 'occurrence_rate', numpy.nan)
        tup = (0, ebrupture.rup_id, ebrupture.source_id, ebrupture.et_id,
               rup.code, ebrupture.n_occ, rup.mag, rup.rake, rate,
               minlon, minlat, maxlon, maxlat, hypo, 0, 0, 0)
        rups.append(tup)
        # we are storing the geometries as arrays of 32 bit floating points;
        # the first element is the number of surfaces, then there are
        # 2 * num_surfaces integers describing the first and second
        # dimension of each surface, and then the lons, lats and deps of
        # the underlying meshes of points.
        geom = numpy.concatenate([[len(shapes) // 2], shapes, points])
        geoms.append(geom)
    if not rups:
        return ()
    dic = dict(geom=numpy.array(geoms, object))
    # NB: PMFs for nonparametric ruptures are not saved since they
    # are useless for the GMF computation
    return hdf5.ArrayWrapper(numpy.array(rups, rupture_dt), dic)


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
        dictionaries with keys rup_array, calc_times, eff_ruptures
    """
    eb_ruptures = []
    ses_seed = param['ses_seed']
    numpy.random.seed(sources[0].serial(ses_seed))
    [et_id] = set(src.et_id for src in sources)
    # AccumDict of arrays with 3 elements nsites, nruptures, calc_time
    calc_times = AccumDict(accum=numpy.zeros(3, numpy.float32))
    # Set the parameters required to compute the number of occurrences
    # of the group of sources
    #  assert param['oqparam'].number_of_logic_tree_samples > 0
    samples = getattr(sources[0], 'samples', 1)
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
    #   only for nons-parametric sources).
    # * The group contains mutually exclusive sources. In this case we
    #   choose one source and then one rupture from this source.
    rup_counter = {}
    rup_data = {}
    for rlz_num in range(grp_num_occ):
        if sources.cluster:
            for src, _ in srcfilter.filter(sources):
                # Track calculation time
                t0 = time.time()
                rup = src.get_one_rupture(ses_seed)
                # The problem here is that we do not know a-priori the
                # number of occurrences of a given rupture.
                if src.id not in rup_counter:
                    rup_counter[src.id] = {}
                    rup_data[src.id] = {}
                if rup.idx not in rup_counter[src.id]:
                    rup_counter[src.id][rup.idx] = 1
                    rup_data[src.id][rup.idx] = [rup, src.id, et_id]
                else:
                    rup_counter[src.id][rup.idx] += 1
                # Store info
                dt = time.time() - t0
                calc_times[src.id] += numpy.array(
                    [len(rup_data[src.id]), src.nsites, dt])
        elif param['src_interdep'] == 'mutex':
            raise NotImplementedError('src_interdep == mutex')
    # Create event based ruptures
    for src_key in rup_data:
        for rup_key in rup_data[src_key]:
            rup, source_id, et_id = rup_data[src_key][rup_key]
            cnt = rup_counter[src_key][rup_key]
            ebr = EBRupture(rup, source_id, et_id, cnt)
            eb_ruptures.append(ebr)

    return eb_ruptures, calc_times


# NB: there is postfiltering of the ruptures, which is more efficient
def sample_ruptures(sources, srcfilter, param, monitor=Monitor()):
    """
    :param sources:
        a sequence of sources of the same group
    :param srcfilter:
        SourceFilter instance used also for bounding box post filtering
    :param param:
        a dictionary of additional parameters including
        ses_per_logic_tree_path
    :param monitor:
        monitor instance
    :yields:
        dictionaries with keys rup_array, calc_times
    """
    # AccumDict of arrays with 3 elements num_ruptures, num_sites, calc_time
    calc_times = AccumDict(accum=numpy.zeros(3, numpy.float32))
    # Compute and save stochastic event sets
    num_ses = param['ses_per_logic_tree_path']
    trt = sources[0].tectonic_region_type
    # Compute the number of occurrences of the source group. This is used
    # for cluster groups or groups with mutually exclusive sources.
    if (getattr(sources, 'atomic', False) and
            getattr(sources, 'cluster', False)):
        eb_ruptures, calc_times = sample_cluster(
            sources, srcfilter, num_ses, param)

        # Yield ruptures
        yield AccumDict(dict(rup_array=get_rup_array(eb_ruptures, srcfilter),
                             calc_times=calc_times,
                             eff_ruptures={trt: len(eb_ruptures)}))
    else:
        eb_ruptures = []
        eff_ruptures = 0
        # AccumDict of arrays with 2 elements weight, calc_time
        calc_times = AccumDict(accum=numpy.zeros(3, numpy.float32))
        for src, _ in srcfilter.filter(sources):
            nr = src.num_ruptures
            eff_ruptures += nr
            t0 = time.time()
            if len(eb_ruptures) > MAX_RUPTURES:
                # yield partial result to avoid running out of memory
                yield AccumDict(dict(rup_array=get_rup_array(eb_ruptures,
                                                             srcfilter),
                                     calc_times={}, eff_ruptures={}))
                eb_ruptures.clear()
            samples = getattr(src, 'samples', 1)
            for rup, et_id, n_occ in src.sample_ruptures(
                    samples * num_ses, param['ses_seed']):
                ebr = EBRupture(rup, src.source_id, et_id, n_occ)
                eb_ruptures.append(ebr)
            dt = time.time() - t0
            calc_times[src.id] += numpy.array([nr, src.nsites, dt])
        rup_array = get_rup_array(eb_ruptures, srcfilter)
        yield AccumDict(dict(rup_array=rup_array, calc_times=calc_times,
                             eff_ruptures={trt: eff_ruptures}))
