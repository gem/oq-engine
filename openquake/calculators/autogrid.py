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
spread over the region (with a single GMPE per group and two IMTs),
both for a reference setting (no gridding and all nodal planes and
hypocenters within 100 km) and for a set of candidate pairs
(ps_grid_spacing, pointsource_distance); the cheapest candidate with a
99th percentile of the relative error on the hazard maps below a
tolerance is chosen.
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
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.contexts import PAIR_COST
from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib.geo.utils import spherical_to_cartesian

GRID_SPACINGS = [50., 25., 15.]  # candidate values in km
PS_DISTANCES = [50., 100.]  # candidate values in km
# reference (ps_grid_spacing, pointsource_distance): no gridding and all
# nodal planes and hypocenters within 100 km; using 1000 km would be
# exact but too expensive with large maximum distances (e.g. in AUS)
REFERENCE = (0., 100.)
TOLERANCE = .05  # on the 99th percentile of the relative error
MIN_HMAP = .01  # ignore the hazard maps below this value (in g)
# the calibration uses only the IMTs with the periods closest to these:
# the largest errors are at 0.2 s in SAM and at 1.0 s in Tonga
PERIODS = [.2, 1.]
NSITES = 300  # size of the sample of sites, if maximum_distance <= MAXDIST
MAXDIST = 300.  # in km, see _get_nsites
MIN_NSITES = 100  # minimum size of the sample of sites
# the points farther than the maximum distance plus MARGIN (in km) from
# all the sample sites are ignored; the margin keeps complete the grid
# cells crossing the maximum distance
MARGIN = 100.


def calib_task(srcs, sites, cmaker, key, monitor):
    """
    :returns: (key, rates averaged on the gsims, [cpu time, weight])

    The weight is computed as in ContextMaker.estimate_weight, from the
    number of contexts and (rupture, site) pairs; unlike the time on the
    sample, it ranks correctly the cost of the full calculation
    """
    t0 = time.time()
    cmaker.init_monitoring(monitor)
    cmaker.tom = PoissonTOM(cmaker.investigation_time)
    sf = SourceFilter(sites, cmaker.oq.maximum_distance)
    rmap = MapArray(sites.sids, cmaker.imtls.size, len(cmaker.gsims),
                    rates=True).fill(0)
    weight = 0
    for src in srcs:
        close = sf.get_close_sites(src)
        if close is not None:
            for ctx in cmaker.get_ctxs(src, close):
                weight += len(ctx)
                cmaker.update(rmap, ctx)
            weight += src.num_ruptures * len(close) / PAIR_COST
    return key, rmap.array.mean(axis=2), numpy.array(
        [time.time() - t0, weight])


# split the area and multipoint sources in point sources, keeping only
# the points close to the sample sites (a multipoint source without close
# points is not split at all); the point sources of the composite source
# model are not modified; a source with a single point is not split by
# split_source, so it is not gridded by the engine and it is ignored,
# since it gives no gridding error
def _get_points(sg, kdt, maxdist):
    points = []
    for src in sg:
        if src.code == b'M' and not _close(
                kdt, src.mesh.lons, src.mesh.lats, maxdist).any():
            continue
        if src.code in b'AM' and not src.bysrc_unc:
            points.extend(s for s in split_source(src) if s.code == b'P')
        elif src.code == b'P':
            points.append(src)
    if points:
        close = _close(kdt, [p.location.x for p in points],
                       [p.location.y for p in points], maxdist)
        points = [p for p, c in zip(points, close) if c]
    return points


# returns a boolean array, True for the locations within the maximum
# distance plus MARGIN from some site
def _close(kdt, lons, lats, maxdist):
    xyz = spherical_to_cartesian(lons, lats, numpy.zeros(len(lons)))
    nsites = kdt.query_ball_point(xyz, maxdist + MARGIN, return_length=True)
    return nsites > 0


# split the sources of the groups, gridded with the given spacing, in
# blocks (weight, srcs) for each group; the blocks are balanced by number
# of ruptures times number of sites within the maximum distance from the
# location of the source
def _get_blocks(groups, sites, cmakers, psgs, num_tasks):
    kdt = KDTree(sites.xyz)
    pairs = {}  # grp_id -> [(src, weight), ...]
    for grp_id, points in groups.items():
        srcs = grid_point_sources(points, psgs) if psgs else points
        for src in srcs:
            if not hasattr(src, 'id'):  # new CollapsedPointSource
                src.id = src.offset = 0  # needed to build the contexts
        locs = numpy.array([(src.location.x, src.location.y,
                             src.location.z) for src in srcs])
        nsites = kdt.query_ball_point(
            spherical_to_cartesian(*locs.T), _maxdist(cmakers[grp_id]),
            return_length=True)
        pairs[grp_id] = [(src, src.num_ruptures * (n + 1))
                         for src, n in zip(srcs, nsites)]
    tot = sum(w for prs in pairs.values() for _, w in prs)
    return {grp_id: [(blk.weight, [src for src, _ in blk])
                     for blk in block_splitter(prs, tot / num_tasks,
                                               lambda p: p[1])]
            for grp_id, prs in pairs.items()}


# yield pairs (weight, args) for the calibration tasks of the candidate
# (psgs, psd), given the blocks of sources gridded with spacing psgs
def _gen_args(blocks, sites, cmakers, psgs, psd):
    for grp_id, blks in blocks.items():
        cmaker = copy.copy(cmakers[grp_id])
        cmaker.pointsource_distance = psd
        for weight, srcs in blks:
            yield weight, (srcs, sites, cmaker, (psgs, psd))


# the IMTs with the periods closest to PERIODS, or all the IMTs if
# there are less than 3 IMTs of kind PGA or SA
def _calib_imts(imtls):
    imts = [imt for imt in imtls if imt == 'PGA' or imt.startswith('SA(')]
    if len(imts) < 3:
        return list(imtls)
    periods = numpy.array([from_string(imt).period for imt in imts])
    chosen = {imts[numpy.abs(periods - period).argmin()]
              for period in PERIODS}
    return [imt for imt in imtls if imt in chosen]


# ContextMakers with a single GMPE and two IMTs (see PERIODS): the error
# of the gridding is geometric and does not depend much on the GMPE,
# while the cost of the calibration is proportional to the number of
# GMPEs and IMTs
def _calib_cmakers(cmakers, groups):
    out = {}
    for grp_id in groups:
        cmaker = cmakers[grp_id].restrict(
            _calib_imts(cmakers[grp_id].imtls))
        gsim, rlzs = next(iter(cmaker.gsims.items()))
        cmaker.gsims = {gsim: rlzs}
        out[grp_id] = cmaker
    return out


# maximum distance of the given ContextMaker
def _maxdist(cmaker):
    return max(d for _, d in cmaker.oq.maximum_distance[cmaker.trt])


# the cost of each site grows with the area within the maximum distance,
# so the size of the sample is reduced for large maximum distances
def _get_nsites(groups, cmakers):
    maxdist = max(_maxdist(cmakers[grp_id]) for grp_id in groups)
    ratio = min(1., (MAXDIST / maxdist) ** 2)
    return max(MIN_NSITES, int(NSITES * ratio))


def sample_sites(sitecol, nsites=NSITES):
    """
    :returns: around nsites sites evenly spread over the region, obtained
              by taking every n-th site in geohash order
    """
    step = int(numpy.ceil(len(sitecol) / nsites))
    idx = numpy.sort(numpy.argsort(sitecol.geohash(8))[::step])
    sites = SiteCollection.from_(sitecol.array[idx])
    sites.make_complete()  # reset the sids from 0 to len(sites) - 1
    return sites


def calibrate(csm, cmakers, sitecol, oq, h5=None):
    """
    Determine ps_grid_spacing and pointsource_distance by comparing the
    hazard maps of the point sources on a sample of sites with the
    reference ones. All the grid spacings are tried, each one with the
    distances from the smallest (the cheapest) up to the first within
    the tolerance; the candidate within the tolerance with the smallest
    weight is chosen. NB: the largest spacing is not always the
    cheapest, since big cells make more sites close to the sources.

    :returns: (ps_grid_spacing, pointsource_distance) or None if there
              are no point sources
    """
    sgs = {sg.sources[0].grp_id: sg for sg in csm.src_groups
           if not sg.atomic and any(src.code in b'AMP' for src in sg)}
    if not sgs:
        return None
    if oq.psd_given:
        distances = [oq.pointsource_distance['default']]
    else:
        distances = PS_DISTANCES
    cmakers = _calib_cmakers(cmakers, sgs)
    imtls = cmakers[next(iter(sgs))].imtls
    sites = sample_sites(sitecol, _get_nsites(sgs, cmakers))
    kdt = KDTree(sites.xyz)
    groups = {grp_id: _get_points(sg, kdt, _maxdist(cmakers[grp_id]))
              for grp_id, sg in sgs.items()}
    groups = {grp_id: pts for grp_id, pts in groups.items() if pts}
    if not groups:
        return None
    logging.info('Calibrating ps_grid_spacing among %s and '
                 'pointsource_distance among %s on %d sites with one GMPE '
                 'per group', GRID_SPACINGS, distances, len(sites))
    num_tasks = parallel.num_cores * 2
    ref = None
    rows = []  # (psgs, psd, time, weight, p99, mean)
    blocks = {psgs: _get_blocks(groups, sites, cmakers, psgs, num_tasks)
              for psgs in GRID_SPACINGS}
    pending = GRID_SPACINGS  # spacings without a candidate within tolerance
    for psd in distances:
        logging.info('Trying ps_grid_spacing=%s with pointsource_distance=%s',
                     pending, psd)
        allargs = [args for psgs in pending for args in _gen_args(
            blocks[psgs], sites, cmakers, psgs, psd)]
        if ref is None:  # compute the reference rates in the first round
            refblocks = _get_blocks(
                groups, sites, cmakers, REFERENCE[0], num_tasks)
            allargs.extend(_gen_args(refblocks, sites, cmakers, *REFERENCE))
        rates, costs = _run(allargs, h5)
        if ref is None:
            ref = get_hmaps(rates.pop(REFERENCE), imtls, oq)
            ref_time = costs[REFERENCE][0]
        new = list(_get_rows(rates, costs, ref, imtls, oq))
        rows.extend(new)
        pending = [row[0] for row in new if row[4] > TOLERANCE]
        if not pending:
            break
    lines = ['%5.0f %5.0f %9.1f %11.0f %8.4f %8.4f' % row for row in rows]
    logging.info('Calibration on %d sites (reference time=%.1fs)\n'
                 ' psgs   psd      time      weight      p99     mean\n%s',
                 len(sites), ref_time, '\n'.join(lines))
    good = [row for row in rows if row[4] <= TOLERANCE]
    if good:  # the candidate within the tolerance with the smallest weight
        return min(good, key=lambda row: row[3])[:2]
    return min(rows, key=lambda row: row[4])[:2]  # the most precise


# run the given calibration tasks in parallel; the heaviest tasks are
# submitted first, so that they do not end up last with most of the
# cores idle
def _run(allargs, h5):
    smap = parallel.Starmap(calib_task, h5=h5)
    for _, args in sorted(allargs, key=lambda pair: -pair[0]):
        smap.submit(args)
    rates, costs = AccumDict(accum=0), AccumDict(accum=0)
    for key, rts, cost in smap:
        rates[key] += rts
        costs[key] += cost
    return rates, costs


def get_hmaps(rates, imtls, oq):
    """
    :param rates: an array of shape (N, L)
    :param imtls: a DictArray with M IMTs
    :returns: the hazard maps, an array of shape (N, M, P)
    """
    curves = -numpy.expm1(-rates * oq.investigation_time)
    curves = curves.reshape(len(rates), len(imtls), -1)
    return compute_hmaps(curves, imtls, oq.poes or [.002105])


# yield a row (psgs, psd, time, weight, p99, mean) for each candidate, where
# p99 and mean refer to the relative error on the relevant hazard maps
def _get_rows(rates, costs, ref, imtls, oq):
    ok = ref > MIN_HMAP
    for key in rates:
        hmaps = get_hmaps(rates[key], imtls, oq)
        # if no hazard map is relevant any candidate is good
        errs = numpy.abs(hmaps[ok] - ref[ok]) / ref[ok] if ok.any(
            ) else numpy.zeros(1)
        yield key + tuple(costs[key]) + (
            numpy.percentile(errs, 99), errs.mean())
