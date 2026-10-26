# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
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
Calibration of ps_grid_spacing and pointsource_distance, performed in
preclassical when the user sets ``ps_grid_spacing = auto``.

The rates of the point sources are computed on a sample of sites evenly
spread over the region, both exactly (no gridding, all nodal planes and
hypocenters) and for a set of candidate pairs (ps_grid_spacing,
pointsource_distance); the cheapest candidate with a 99th percentile of
the relative error on the hazard maps below a tolerance is chosen.
"""
import copy
import time
import logging
import numpy
from scipy.spatial import KDTree
from openquake.baselib import parallel
from openquake.baselib.general import AccumDict, block_splitter
from openquake.hazardlib.map_array import MapArray, compute_hmaps
from openquake.hazardlib.source.point import grid_point_sources
from openquake.hazardlib.calc.filters import SourceFilter, split_source
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib.geo.utils import spherical_to_cartesian

GRID_SPACINGS = [50., 25., 15.]  # candidate values in km, cheapest first
PS_DISTANCES = [50., 100.]  # candidate values in km
EXACT = (0., 1000.)  # no gridding, all nodal planes and hypocenters
TOLERANCE = .05  # on the 99th percentile of the relative error
MIN_HMAP = .01  # ignore the hazard maps below this value (in g)
NSITES = 300  # size of the sample of sites


def calib_task(srcs, sites, cmaker, key, monitor):
    """
    :returns: (key, rates averaged on the gsims, cpu time)
    """
    t0 = time.time()
    cmaker.init_monitoring(monitor)
    cmaker.tom = PoissonTOM(cmaker.investigation_time)
    sf = SourceFilter(sites, cmaker.oq.maximum_distance)
    rmap = MapArray(sites.sids, cmaker.imtls.size, len(cmaker.gsims),
                    rates=True).fill(0)
    for src in srcs:
        close = sf.get_close_sites(src)
        if close is not None:
            for ctx in cmaker.get_ctxs(src, close):
                cmaker.update(rmap, ctx)
    return key, rmap.array.mean(axis=2), time.time() - t0


# split the area and multipoint sources in point sources; the point
# sources of the composite source model are not modified
def _get_points(sg):
    points = []
    for src in sg:
        if src.code in b'AM' and not src.bysrc_unc:
            points.extend(split_source(src))
        elif src.code == b'P':
            points.append(src)
    return points


# yield the arguments of the calibration tasks for the given grid spacing
# and distances; the gridding is performed only once; the tasks are
# balanced by number of ruptures times number of sites within the
# maximum distance from the location of the source
def _gen_args(groups, sites, cmakers, psgs, distances, num_tasks):
    kdt = KDTree(sites.xyz)
    pairs = {}  # grp_id -> [(src, weight), ...]
    for grp_id, points in groups.items():
        srcs = grid_point_sources(points, psgs) if psgs else points
        for src in srcs:
            if not hasattr(src, 'id'):  # new CollapsedPointSource
                src.id = src.offset = 0  # needed to build the contexts
        cmaker = cmakers[grp_id]
        maxdist = max(d for _, d in cmaker.oq.maximum_distance[cmaker.trt])
        locs = numpy.array([(src.location.x, src.location.y,
                             src.location.z) for src in srcs])
        nsites = kdt.query_ball_point(
            spherical_to_cartesian(*locs.T), maxdist, return_length=True)
        pairs[grp_id] = [(src, src.num_ruptures * (n + 1))
                         for src, n in zip(srcs, nsites)]
    tot = sum(w for prs in pairs.values() for _, w in prs)
    blocks = {grp_id: [[src for src, _ in block] for block in
                       block_splitter(prs, tot / num_tasks, lambda p: p[1])]
              for grp_id, prs in pairs.items()}
    for psd in distances:
        for grp_id in blocks:
            cmaker = copy.copy(cmakers[grp_id])
            cmaker.pointsource_distance = psd
            for block in blocks[grp_id]:
                yield block, sites, cmaker, (psgs, psd)


def sample_sites(sitecol):
    """
    :returns: around NSITES sites evenly spread over the region, obtained
              by taking every n-th site in geohash order
    """
    step = int(numpy.ceil(len(sitecol) / NSITES))
    idx = numpy.sort(numpy.argsort(sitecol.geohash(8))[::step])
    sites = SiteCollection.from_(sitecol.array[idx])
    sites.make_complete()  # reset the sids from 0 to len(sites) - 1
    return sites


def calibrate(csm, cmakers, sitecol, oq, h5=None):
    """
    Determine ps_grid_spacing and pointsource_distance by comparing the
    hazard maps of the point sources on a sample of sites with the exact
    ones. The grid spacings are tried from the largest (the cheapest) and
    the calibration stops as soon as a candidate is within the tolerance.

    :returns: (ps_grid_spacing, pointsource_distance) or None if there
              are no point sources
    """
    groups = {sg.sources[0].grp_id: _get_points(sg)
              for sg in csm.src_groups if not sg.atomic}
    groups = {grp_id: pts for grp_id, pts in groups.items() if pts}
    if not groups:
        return None
    if oq.psd_given:
        distances = [oq.pointsource_distance['default']]
    else:
        distances = PS_DISTANCES
    sites = sample_sites(sitecol)
    exact = None
    rows = []  # (psgs, psd, time, p99, mean)
    for psgs in GRID_SPACINGS:
        cands = [(psgs, distances)]
        if exact is None:  # compute the exact rates in the first round
            cands.append((EXACT[0], [EXACT[1]]))
        rates, times = _run(cands, groups, sites, cmakers, h5)
        if exact is None:
            exact = get_hmaps(rates.pop(EXACT), oq)
            exact_time = times[EXACT]
        rows.extend(_get_rows(rates, times, exact, oq))
        good = [row for row in rows if row[3] <= TOLERANCE]
        if good:
            break
    lines = ['%5.0f %5.0f %9.1f %8.4f %8.4f' % row for row in rows]
    logging.info('Calibration on %d sites (exact time=%.1fs)\n'
                 ' psgs   psd      time      p99     mean\n%s',
                 len(sites), exact_time, '\n'.join(lines))
    if good:  # the cheapest candidate within the tolerance
        return min(good, key=lambda row: row[2])[:2]
    return min(rows, key=lambda row: row[3])[:2]  # the most precise


# run the calibration tasks for the given candidates in parallel
def _run(cands, groups, sites, cmakers, h5):
    num_tasks = parallel.num_cores * 2
    smap = parallel.Starmap(calib_task, h5=h5)
    for psgs, distances in cands:
        for args in _gen_args(
                groups, sites, cmakers, psgs, distances, num_tasks):
            smap.submit(args)
    rates, times = AccumDict(accum=0), AccumDict(accum=0)
    for key, rts, dt in smap:
        rates[key] += rts
        times[key] += dt
    return rates, times


def get_hmaps(rates, oq):
    """
    :param rates: an array of shape (N, L)
    :returns: the hazard maps, an array of shape (N, M, P)
    """
    curves = -numpy.expm1(-rates * oq.investigation_time)
    curves = curves.reshape(len(rates), len(oq.imtls), -1)
    return compute_hmaps(curves, oq.imtls, oq.poes or [.002105])


# yield a row (psgs, psd, time, p99, mean) for each candidate, where
# p99 and mean refer to the relative error on the relevant hazard maps
def _get_rows(rates, times, exact, oq):
    ok = exact > MIN_HMAP
    for key in rates:
        hmaps = get_hmaps(rates[key], oq)
        # if no hazard map is relevant any candidate is good
        errs = numpy.abs(hmaps[ok] - exact[ok]) / exact[ok] if ok.any(
            ) else numpy.zeros(1)
        yield key + (times[key], numpy.percentile(errs, 99), errs.mean())
