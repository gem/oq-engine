# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2018 GEM Foundation
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
from openquake.hazardlib.source.rupture import BaseRupture, EBRupture
from openquake.hazardlib.contexts import ContextMaker, FarAwayRupture
from openquake.hazardlib.geo.mesh import surface_to_array, point3d

TWO16 = 2 ** 16  # 65,536
TWO32 = 2 ** 32  # 4,294,967,296
F64 = numpy.float64
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
U8 = numpy.uint8
I32 = numpy.int32
F32 = numpy.float32
MAX_RUPTURES = 1000


def source_site_noop_filter(srcs):
    for src in srcs:
        yield src, None


source_site_noop_filter.integration_distance = {}


# this is used in acceptance/stochastic_test.py, not in the engine
def stochastic_event_set(sources, source_site_filter=source_site_noop_filter):
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
    for source, s_sites in source_site_filter(sources):
        try:
            for rupture in source.iter_ruptures():
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
    ('serial', U32), ('srcidx', U16), ('grp_id', U16), ('code', U8),
    ('n_occ', U16), ('mag', F32), ('rake', F32), ('occurrence_rate', F32),
    ('minlon', F32), ('minlat', F32), ('maxlon', F32), ('maxlat', F32),
    ('hypo', (F32, 3)), ('gidx1', U32), ('gidx2', U32),
    ('sy', U16), ('sz', U16)])


# this is really fast
def get_rup_array(ebruptures, srcfilter):
    """
    Convert a list of EBRuptures into a numpy composite array, by filtering
    out the ruptures far away from every site
    """
    if not BaseRupture._code:
        BaseRupture.init()  # initialize rupture codes

    rups = []
    geoms = []
    nbytes = 0
    offset = 0
    for ebrupture in ebruptures:
        rup = ebrupture.rupture
        mesh = surface_to_array(rup.surface)
        sy, sz = mesh.shape[1:]  # sanity checks
        assert sy < TWO16, 'Too many multisurfaces: %d' % sy
        assert sz < TWO16, 'The rupture mesh spacing is too small'
        points = mesh.reshape(3, -1).T   # shape (n, 3)
        minlon = points[:, 0].min()
        minlat = points[:, 1].min()
        maxlon = points[:, 0].max()
        maxlat = points[:, 1].max()
        hypo = rup.hypocenter.x, rup.hypocenter.y, rup.hypocenter.z
        rate = getattr(rup, 'occurrence_rate', numpy.nan)
        tup = (ebrupture.serial, ebrupture.srcidx, ebrupture.grp_id,
               rup.code, ebrupture.n_occ, rup.mag, rup.rake, rate,
               minlon, minlat, maxlon, maxlat,
               hypo, offset, offset + len(points), sy, sz)
        offset += len(points)
        rups.append(tup)
        geoms.append(numpy.array([tuple(p) for p in points], point3d))
        nbytes += rupture_dt.itemsize + mesh.nbytes
    if not rups:
        return ()
    dic = dict(geom=numpy.concatenate(geoms), nbytes=nbytes)
    # TODO: PMFs for nonparametric ruptures are not converted
    return hdf5.ArrayWrapper(numpy.array(rups, rupture_dt), dic)


def sample_ruptures(sources, param, src_filter=source_site_noop_filter,
                    monitor=Monitor()):
    """
    :param sources:
        a sequence of sources of the same group
    :param param:
        a dictionary of additional parameters including rlzs_by_gsim,
        ses_per_logic_tree_path and filter_distance
    :param src_filter:
        a source site filter
    :param monitor:
        monitor instance
    :yields:
        dictionaries with keys rup_array, calc_times, eff_ruptures
    """
    # AccumDict of arrays with 3 elements weight, nsites, calc_time
    calc_times = AccumDict(accum=numpy.zeros(3, numpy.float32))
    # Compute and save stochastic event sets
    cmaker = ContextMaker(param['gsims'],
                          src_filter.integration_distance,
                          param, monitor)
    num_ses = param['ses_per_logic_tree_path']
    eff_ruptures = 0
    grp_id = sources[0].src_group_id
    eb_ruptures = []
    for src, sites in src_filter(sources):
        t0 = time.time()
        if len(eb_ruptures) > MAX_RUPTURES:
            rup_array = get_rup_array(eb_ruptures, src_filter)
            yield AccumDict(
                rup_array=rup_array, calc_times={}, eff_ruptures={})
            eb_ruptures.clear()
        ebrs = build_eb_ruptures(src, num_ses, cmaker, sites)
        n_occ = sum(ebr.n_occ for ebr in ebrs)
        eb_ruptures.extend(ebrs)
        eff_ruptures += src.num_ruptures
        dt = time.time() - t0
        calc_times[src.id] += numpy.array([n_occ, src.nsites, dt])
    rup_array = get_rup_array(eb_ruptures, src_filter)
    yield AccumDict(rup_array=rup_array,
                    calc_times=calc_times,
                    eff_ruptures={grp_id: eff_ruptures})


def build_eb_ruptures(src, num_ses, cmaker, s_sites, rup_n_occ=()):
    """
    :param src: a source object
    :param num_ses: number of stochastic event sets
    :param cmaker: a ContextMaker instance
    :param s_sites: a (filtered) site collection
    :param rup_n_occ: (rup, n_occ) pairs [inferred from the source]
    :returns: a list of EBRuptures
    """
    ebrs = []
    samples = getattr(src, 'samples', 1)
    if rup_n_occ == ():
        # NB: the number of occurrences is very low, << 1, so it is
        # more efficient to filter only the ruptures that occur, i.e.
        # to call sample_ruptures *before* the filtering
        rup_n_occ = src.sample_ruptures(samples, num_ses, cmaker.ir_mon)
    for rup, n_occ in rup_n_occ:
        if cmaker.maximum_distance:
            with cmaker.ctx_mon:
                try:
                    cmaker.filter(s_sites, rup)
                except FarAwayRupture:
                    continue
        ebrs.append(EBRupture(rup, src.id, src.src_group_id, n_occ, samples))
    return ebrs
