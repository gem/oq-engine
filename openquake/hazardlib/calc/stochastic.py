# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
import time
import numpy
import shapely
from openquake.baselib import hdf5
from openquake.baselib.general import AccumDict, random_histogram
from openquake.baselib.performance import Monitor
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

# ######################## rupture calculator ############################ #


# this is really fast
def get_rup_array(ebruptures, srcfilter=nofilter, model='???', model_geom=None):
    """
    Convert a list of EBRuptures into a numpy composite array, by filtering
    out the ruptures far away from every site. If a shapely polygon is passed
    in model_geom, ruptures outside the polygon are discarded.
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
        rec['id'] = ebrupture.id
        rec['seed'] = ebrupture.seed
        rec['minlon'] = minlon = numpy.nanmin(lons)  # NaNs are in KiteSurfaces
        rec['minlat'] = minlat = numpy.nanmin(lats)
        rec['maxlon'] = maxlon = numpy.nanmax(lons)
        rec['maxlat'] = maxlat = numpy.nanmax(lats)
        rec['mag'] = rup.mag
        rec['hypo'] = hypo
        rec['model'] = model

        # apply magnitude filtering
        if srcfilter.integration_distance(rup.mag) == 0:
            continue

        # apply distance filtering
        nsites = 0
        if srcfilter.sitecol is not None:
            nsites = len(srcfilter.close_sids(rec, rup.tectonic_region_type))
            if nsites == 0:
                continue

        # apply model filtering if any (used in `oq mosaic sample_rups`)
        if model_geom and not shapely.contains_xy(
                model_geom, hypo[0], hypo[1]):
            continue

        rate = getattr(rup, 'occurrence_rate', numpy.nan)
        tup = (ebrupture.id, ebrupture.seed, ebrupture.source_id,
               ebrupture.trt_smr, rup.code, ebrupture.n_occ, rup.mag, rup.rake,
               rate, minlon, minlat, maxlon, maxlat, hypo, 0, nsites, 0, model)
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
    arr = numpy.array(rups, rupture_dt)
    return hdf5.ArrayWrapper(arr, dic)


def sample_cluster(group, num_ses, ses_seed):
    """
    Yields ruptures generated by a cluster of sources

    :param group:
        A sequence of sources of the same group
    :param num_ses:
        Number of stochastic event sets
    :param ses_seed:
        Global seed for rupture sampling
    :yields:
        dictionaries with keys rup_array, source_data, eff_ruptures
    """
    eb_ruptures = []
    seed = group[0].serial(ses_seed)
    rng = numpy.random.default_rng(seed)
    [trt_smr] = set(src.trt_smr for src in group)
    # Set the parameters required to compute the number of occurrences
    # of the group of group
    samples = getattr(group[0], 'samples', 1)
    grp_probability = getattr(group, 'grp_probability', 1.)
    tom = group.temporal_occurrence_model
    rate = getattr(tom, 'occurrence_rate', None)
    if rate is None:  # time dependent sources
        tot_num_occ = rng.poisson(grp_probability * samples * num_ses)
    else:  # poissonian sources with ClusterPoissonTOM
        tot_num_occ = rng.poisson(rate * tom.time_span * samples * num_ses)

    # Now we process the sources included in the group. Possible cases:
    # * The group contains nonparametric sources with mutex ruptures, while
    #   the sources are indepedent.
    # * The group contains mutually exclusive sources. In this case we
    #   choose the source first and then some ruptures from the source.
    if group.rup_interdep == 'mutex' and group.src_interdep == 'indep':
        allrups = []
        weights = []
        rupids = []
        for src in group:
            rupids.extend(src.offset + numpy.arange(src.num_ruptures))
            weights.extend(src.rup_weights)
            src_seed = src.serial(ses_seed)
            for i, rup in enumerate(src.iter_ruptures()):
                rup.src_id = src.id
                allrups.append(rup)
        # random distribute in bins according to the rup_weights
        n_occs = random_histogram(tot_num_occ, weights, seed)
        for rup, rupid, n_occ in zip(allrups, rupids, n_occs):
            if n_occ:
                ebr = EBRupture(rup, rup.src_id, trt_smr, n_occ, rupid)
                ebr.seed = ebr.id + ses_seed
                eb_ruptures.append(ebr)

    elif group.src_interdep == 'mutex' and group.rup_interdep == 'indep':
        # random distribute in bins according to the srcs_weights
        ws = [src.mutex_weight for src in group]
        src_occs = random_histogram(tot_num_occ, ws, seed)
        # NB: in event_based/src_mutex num_ses=2000, samples=1
        # and there are 10 sources with weights
        # 0.368, 0.061, 0.299, 0.049, 0.028, 0.011, 0.011, 0.018, 0.113, 0.042
        # => src_occs = [758, 120, 600,  84,  58,  16,  24,  28, 230,  82]
        for src, src_occ in zip(group, src_occs):
            src_seed = src.serial(ses_seed)
            # random distribute in bins equally
            n_occs = random_histogram(src_occ, src.num_ruptures, src_seed)
            rseeds = src_seed + numpy.arange(src.num_ruptures)
            rupids = src.offset + numpy.arange(src.num_ruptures)
            for rup, rupid, n_occ, rseed in zip(
                    src.iter_ruptures(), rupids, n_occs, rseeds):
                if n_occ:
                    ebr = EBRupture(rup, src.id, trt_smr, n_occ, rupid)
                    ebr.seed = ebr.id + ses_seed
                    eb_ruptures.append(ebr)
    else:
        raise NotImplementedError(
            f'{group.src_interdep=}, {group.rup_interdep=}')
    return eb_ruptures


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
    model = getattr(cmaker, 'model', '???')
    model_geom = getattr(cmaker, 'model_geom', None)
    srcfilter = SourceFilter(sitecol, cmaker.maximum_distance)
    # AccumDict of arrays with 3 elements nsites, nruptures, calc_time
    source_data = AccumDict(accum=[])
    # Compute and save stochastic event sets
    num_ses = cmaker.ses_per_logic_tree_path
    grp_id = sources[0].grp_id
    # Compute the number of occurrences of the source group. This is used
    # for cluster groups or groups with mutually exclusive sources.
    if getattr(sources, 'atomic', False):
        t0 = time.time()
        eb_ruptures = sample_cluster(sources, num_ses, cmaker.ses_seed)
        dt = time.time() - t0

        # populate source_data
        tot = sum(src.num_ruptures for src in sources)
        for src in sources:
            source_data['src_id'].append(src.source_id)
            source_data['nsites'].append(src.nsites)
            source_data['nrups'].append(src.num_ruptures)
            source_data['ctimes'].append(dt * src.num_ruptures / tot)
            source_data['weight'].append(src.weight)
            source_data['taskno'].append(monitor.task_no)

        # Yield ruptures
        er = sum(src.num_ruptures for src in sources)
        dic = dict(
            rup_array=get_rup_array(eb_ruptures, srcfilter, model, model_geom),
            source_data=source_data, eff_ruptures={grp_id: er})
        yield AccumDict(dic)
    else:
        eb_ruptures = []
        eff_ruptures = 0
        source_data = AccumDict(accum=[])
        for src in sources:
            nr = src.num_ruptures
            eff_ruptures += nr
            if len(eb_ruptures) > MAX_RUPTURES:
                # yield partial result to avoid running out of memory
                yield AccumDict(dict(
                    rup_array=get_rup_array(
                        eb_ruptures, srcfilter, model, model_geom),
                    source_data={}, eff_ruptures={}))
                eb_ruptures.clear()
            samples = getattr(src, 'samples', 1)
            t0 = time.time()
            eb_ruptures.extend(
                src.sample_ruptures(samples * num_ses, cmaker.ses_seed))
            dt = time.time() - t0
            source_data['src_id'].append(src.source_id)
            source_data['nsites'].append(src.nsites)
            source_data['nrups'].append(nr)
            source_data['ctimes'].append(dt)
            source_data['weight'].append(src.weight)
            source_data['taskno'].append(monitor.task_no)
        t0 = time.time()
        rup_array = get_rup_array(eb_ruptures, srcfilter, model, model_geom)
        dt = time.time() - t0
        if len(rup_array):
            yield AccumDict(dict(rup_array=rup_array, source_data=source_data,
                                 eff_ruptures={grp_id: eff_ruptures}))
